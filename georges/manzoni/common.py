import numpy as np
from .constants import *
from .. import fermi
from .. import physics
from .. import model as _model

FERMI_DB = fermi.MaterialsDB()


def convert_line(line, context={}, to_numpy=True, fermi_params={}):
    def class_conversion(e):
        if e['CLASS'] in ('RFCAVITY',):
            e['CLASS_CODE'] = CLASS_CODES['DRIFT']
        if e['CLASS'] not in CLASS_CODES:
            e['CLASS_CODE'] = CLASS_CODES['NONE']
        else:
            e['CLASS_CODE'] = CLASS_CODES[e['CLASS']]
        return e

    def circuit_conversion(e):
        if e['PLUG'] in INDEX and e['PLUG'] != 'APERTURE':
            e[e['PLUG']] = context.get(e['CIRCUIT'], 0.0)
        return e

    def apertype_conversion(e):
        # Default aperture
        if 'APERTYPE' not in e.index.values:
            e['APERTYPE_CODE'] = APERTYPE_CODE_NONE
            e['APERTURE'] = 0.0
            e['APERTURE_2'] = 0.0
            return e
        # Aperture types
        if e['APERTYPE'] == 'CIRCLE':
            e['APERTYPE_CODE'] = APERTYPE_CODE_CIRCLE
        elif e['APERTYPE'] == 'RECTANGLE':
            e['APERTYPE_CODE'] = APERTYPE_CODE_RECTANGLE
        else:
            e['APERTYPE_CODE'] = APERTYPE_CODE_NONE
            e['APERTURE'] = 0.0
            e['APERTURE_2'] = 0.0
        # Aperture sizes
        if not isinstance(e['APERTURE'], str):
            if np.isnan(e['APERTURE']) and e['PLUG'] == 'APERTURE':
                s = e['CIRCUIT'].strip('[{}]').split(',')
                if context.get(s[0]) is not None:
                    e['APERTURE'] = float(context.get(s[0]))
                else:
                    e['APERTURE'] = 1.0
                if len(s) > 1:
                    e['APERTURE_2'] = float(context.get(s[1], 1.0))
                else:
                    e['APERTURE_2'] = 1.0
        else:
            s = e['APERTURE'].strip('[{}]').split(',')
            e['APERTURE'] = float(s[0])
            if len(s) > 1:
                e['APERTURE_2'] = float(s[1])
        return e

    def fermi_eyges_computations(e):
        if e['CLASS'] != 'DEGRADER' and e['CLASS'] != 'SCATTERER':
            return e
        material = e['MATERIAL']
        if str(material) == '' or str(material) == 'vacuum':
            return e
        fe = fermi.compute_fermi_eyges(material=str(material),
                                       energy=e['ENERGY_IN'],
                                       thickness=100*e['LENGTH'],
                                       db=FERMI_DB,
                                       t=fermi.DifferentialMoliere,
                                       with_dpp=fermi_params.get('with_dpp', True),
                                       with_losses=fermi_params.get('with_losses', True),
                                       )
        e['FE_A0'] = fe['A'][0]
        e['FE_A1'] = fe['A'][1]
        e['FE_A2'] = fe['A'][2]
        e['FE_DPP'] = fe['DPP']
        e['FE_LOSS'] = fe['LOSS']
        return e

    # Create or copy missing columns
    line_copy = line.copy()
    if 'CLASS' not in line_copy and 'KEYWORD' in line_copy:
        line_copy['CLASS'] = line_copy['KEYWORD']
    if 'CLASS' not in line_copy and 'TYPE' in line_copy:
        line_copy['CLASS'] = line_copy['KEYWORD']

    # Fill with zeros
    for i in INDEX.keys():
        if i not in line_copy:
            line_copy[i] = 0.0
    # Perform the conversion
    line_copy = line_copy.apply(class_conversion, axis=1)
    line_copy = line_copy.apply(circuit_conversion, axis=1)
    line_copy = line_copy.apply(apertype_conversion, axis=1)

    # Energy tracking
    if 'BRHO' not in line.columns:
        if context.get('ENERGY'):
            energy = context['ENERGY']
        elif context.get('PC'):
            energy = physics.momentum_to_energy(context['PC'])
        fermi.track_energy(energy, line_copy, FERMI_DB)
        line_copy['BRHO'] = physics.energy_to_brho(line_copy['ENERGY_IN'])

    # Compute Fermi-Eyges parameters
    line_copy = line_copy.apply(fermi_eyges_computations, axis=1)

    # Adjustments for the final format
    line_copy = line_copy.fillna(0.0)
    if to_numpy:
        return line_copy[list(INDEX.keys())].values
    else:
        return line_copy[list(INDEX.keys())+['ENERGY_IN', 'ENERGY_OUT']]


def transform_variables(line, variables):
    ll = line.reset_index()

    def transform(v):
        i = ll[ll['NAME'] == v[0]].index.values[0]
        j = INDEX[v[1]]
        return [i, j]
    return list(map(transform, variables))


def adjust_line(line, variables, parameters):
    it = np.nditer(parameters, flags=['f_index'])
    while not it.finished:
        line[variables[it.index][0], variables[it.index][1]] = it[0]
        it.iternext()
    return line


def transform_elements(line, elements):
    ll = line.reset_index()

    def transform(e):
        return ll[ll['NAME'] == e].index.values[0]
    return list(map(transform, elements))


def _process_model_argument(model, line, beam, context, exception):
    manzoni_line = None
    manzoni_beam = None
    if model is None:
        if line is None or beam is None:
            raise exception("Beamline and Beam objects need to be defined.")
        else:
            if isinstance(line, _model.ManzoniModel):
                raise exception("The line must be a regular Beamline, not a converted Manzoni line.")
            manzoni_line = convert_line(line.line, context)
            manzoni_beam = np.array(beam.distribution)
    else:
        # Access the object's model
        if not isinstance(model, _model.ManzoniModel) and hasattr(model, 'manzoni_model'):
            if hasattr(model, 'model'):
                line = model.model.beamline
            else:
                raise exception("The model must also contain a regular Beamline object.")
            model = model.manzoni_model

        elif not isinstance(model, _model.Model) and hasattr(model, 'model'):
            model = model.model

        # Access or convert the beam and beamline to Manzoni's format
        if isinstance(model, _model.ManzoniModel):
            manzoni_line = model.beamline
            manzoni_beam = model.beam
        elif isinstance(model, _model.Model):
            line = model.beamline
            beam = model.beam
            context = model.context
            manzoni_line = convert_line(line.line, context)
            manzoni_beam = np.array(beam.distribution)

        return {
            'line': manzoni_line,
            'beam': manzoni_beam,
        }