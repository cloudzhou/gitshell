export PYTHONPATH=/opt/app/8001:$PYTHONPATH
export DJANGO_SETTINGS_MODULE=gitshell.settings

for py in `find .|grep py$`
do
    python $py
done
