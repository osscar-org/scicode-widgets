To run the example `notebook1.ipynb` please first run in the root folder (`../`)
```bash
pip install tox
tox -e tests-lab-3
```
After that you can use this environment
```bash
source .tox/tests-lab-3/bin/activate
pip install chemiscope ase markdown
```
to run the examples
```bash
jupyter lab
```
