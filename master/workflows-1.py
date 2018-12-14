from nibetaseries.workflows.base import init_single_subject_wf
wf = init_single_subject_wf(
    atlas_img='',
    atlas_lut='',
    bold_metadata_list=[''],
    brainmask_list=[''],
    confound_tsv_list=[''],
    events_tsv_list=[''],
    hrf_model='glover',
    low_pass=None,
    name='subtest',
    output_dir='.',
    preproc_img_list=[''],
    selected_confounds=[''],
    smoothing_kernel=None)