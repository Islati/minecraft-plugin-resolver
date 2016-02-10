from invoke import task, run


@task
def test(file=None, test=None, k=None):
    run('python setup.py clean build install')
    if k is not None:
        run('py.test -s -k %s' % k)
    elif file is None and test is None:
        run('py.test -s')
    elif file is not None or test is not None:
        if file is not None and test is None:
            run('py.test -s %s' % file)
        elif file is not None and test is not None:
            run('py.test -s %s::%s' % (file, test))
