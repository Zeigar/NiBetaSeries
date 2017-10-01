#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
NiBetaSeries processing workflows
"""
from __future__ import print_function, division, absolute_import, unicode_literals
import sys
import os
from copy import deepcopy
from .util import collect_data
from .preprocess import init_derive_residuals_wf
from niworkflows.nipype.pipeline import engine as pe
from niworkflows.nipype.interfaces import utility as niu
import pkg_resources as pkgr
from bids.grabbids import BIDSLayout


def init_nibetaseries_participant_wf(bids_dir, confound_names, derivatives_pipeline,
                                     exclude_variant, hrf_model, low_pass, omp_nthreads,
                                     output_dir, regfilt, res, run_id, run_uuid, ses_id,
                                     slice_time_ref, smooth, space, subject_list, task_id,
                                     variant, work_dir):
    """
    This workflow organizes the execution of NiBetaSeries, with a sub-workflow for
    each subject.
    .. workflow::
        from NiBetaSeries.workflows.base import init_nibetaseries_participant_wf
        wf = init_nibetaseries_participant_wf(subject_list=['NiBetaSeriesSubsTest'],
                              task_id='',
                              derivatives_pipeline='.',
                              bids_dir='.',
                              output_dir='.',
                              work_dir='.',
                              space='',
                              variant='',
                              res='',
                              hrf_model='glover',
                              slice_time_ref='0.5',
                              run_uuid='X',
                              omp_nthreads=1)
    Parameters
        subject_list : list
            List of subject labels
        task_id : str or None
            Task ID of preprocessed BOLD series to derive betas, or ``None`` to process all
        derivatives_pipeline : str
            Directory where preprocessed derivatives live
        bids_dir : str
            Root directory of BIDS dataset
        output_dir : str
            Directory in which to save derivatives
        work_dir : str
            Directory in which to store workflow execution state and temporary files
        space : str
            Space of preprocessed BOLD series to derive betas, or ``None`` to process all
        variant : str
            Variant of preprocessed BOLD series to derive betas, or ``None`` to process all
        res : str
            resolution (XxYxZ) of preprocessed BOLD series to derive betas, or
            ``None`` to process all
        hrf_model : str
            hrf model used to convolve events
        slice_time_ref : float
            fractional representation of the slice that used as the reference
            during slice time correction.
        run_uuid : str
            Unique identifier for execution instance
        omp_nthreads : int
            Maximum number of threads an individual process may use
    """
    nibetaseries_participant_wf = pe.Workflow(name='nibetaseries_participant_wf')
    nibetaseries_participant_wf.base_dir = os.path.join(work_dir, 'NiBetaSeries_work')
    reportlets_dir = os.path.join(work_dir, 'reportlets')
    bids_deriv_config = pkgr.resource_filename('NiBetaSeries', 'data/bids_derivatives.json')
    derivatives_dir = os.path.join(bids_dir, 'derivatives', derivatives_pipeline)
    derivatives_layout = BIDSLayout(derivatives_dir, config=bids_deriv_config)
    bids_layout = BIDSLayout(bids_dir)

    for subject_id in subject_list:
        deriv_subject_data = collect_data(derivatives_layout,
                                          subject_id,
                                          task=task_id,
                                          run=run_id,
                                          ses=ses_id,
                                          space=space,
                                          deriv=True)

        bids_subject_data = collect_data(bids_layout,
                                         subject_id,
                                         task=task_id,
                                         run=run_id,
                                         ses=ses_id)
        # if you want to avoid using the ICA-AROMA variant
        if exclude_variant:
            deriv_subject_data['preproc'] = [
                preproc for preproc in deriv_subject_data['preproc'] if variant not in preproc
            ]
        # if you only want to use a particular variant
        if variant:
            deriv_subject_data['preproc'] = [
                preproc for preproc in deriv_subject_data['preproc'] if variant in preproc
            ]

        # make sure the lists are the same length
        # pray to god that they are in the same order?
        # ^they appear to be in the same order
        length = len(deriv_subject_data['preproc'])
        print('\n'+subject_id)
        print('preproc:{}'.format(str(length)))
        print('confounds:{}'.format(str(len(deriv_subject_data['confounds']))))
        print('brainmask:{}'.format(str(len(deriv_subject_data['brainmask']))))
        print('AROMAnoiseICs:{}'.format(str(len(deriv_subject_data['AROMAnoiseICs']))))
        print('MELODICmix:{}'.format(str(len(deriv_subject_data['MELODICmix']))))
        print('events:{}'.format(str(len(bids_subject_data['events']))))

        if any(len(lst) != length for lst in [deriv_subject_data['brainmask'],
                                              deriv_subject_data['confounds'],
                                              deriv_subject_data['AROMAnoiseICs'],
                                              deriv_subject_data['MELODICmix'],
                                              bids_subject_data['events']]):
            raise ValueError('input lists are not the same length!')

        single_subject_wf = init_single_subject_wf(
            AROMAnoiseICs=deriv_subject_data['AROMAnoiseICs'],
            brainmask=deriv_subject_data['brainmask'],
            confounds=deriv_subject_data['confounds'],
            confound_names=confound_names,
            events=bids_subject_data['events'],
            hrf_model=hrf_model,
            low_pass=low_pass,
            MELODICmix=deriv_subject_data['MELODICmix'],
            name='single_subject' + subject_id + '_wf',
            preproc=deriv_subject_data['preproc'],
            regfilt=regfilt,
            res=res,
            run_id=run_id,
            run_uuid=run_uuid,
            ses_id=ses_id,
            smooth=smooth,
            space=space,
            subject_id=subject_id,
            slice_time_ref=slice_time_ref,
            task_id=task_id,
            variant=variant
        )

        single_subject_wf.config['execution']['crashdump_dir'] = (
            os.path.join(output_dir, "nibetaseries", "sub-" + subject_id, 'log', run_uuid)
        )

        for node in single_subject_wf._get_all_nodes():
            node.config = deepcopy(single_subject_wf.config)

        nibetaseries_participant_wf.add_nodes([single_subject_wf])
    return nibetaseries_participant_wf


def init_single_subject_wf(AROMAnoiseICs, brainmask, confounds, confound_names,
                           events, hrf_model, low_pass, MELODICmix,
                           name, preproc, regfilt, res, result_dir, run_id, run_uuid,
                           ses_id, smooth, space, subject_id, slice_time_ref, task_id,
                           variant):

    single_subject_wf = pe.Workflow(name=name)

    return single_subject_wf
