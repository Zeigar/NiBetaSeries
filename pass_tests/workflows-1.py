from nibetaseries.workflows.base import init_single_subject_wf
wf = init_single_subject_wf(
    atlas_img='',
    atlas_lut='',
    brainmask_list=[''],
    confound_tsv_list=[''],
    events_tsv_list=[''],
    high_pass='',
    hrf_model='',
    low_pass='',
    name='subtest',
    preproc_img_list=[''],
    selected_confounds=[''],
    smoothing_kernel=0.0)