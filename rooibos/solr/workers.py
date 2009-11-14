from rooibos.workers import register_worker, run_worker

@register_worker('echo')
def echo_worker(job):
    return job.arg


def echo(arg):
    return run_worker('echo', arg)
