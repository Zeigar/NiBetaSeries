from nibetaseries.workflows.model import init_betaseries_wf
wf = init_betaseries_wf(
    hrf_model='glover',
    low_pass=None,
    smoothing_kernel=0.0,
    selected_confounds=[''])