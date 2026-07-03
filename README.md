# ebmlit

## Dependencies

```shell

python -m pip install -r requirements.txt

```

## yearlyscurves

Show default scurve parameters with building code and area parameters.

Make sure to define EBM_INPUT_DIRECTORY in `.env`

```ini
EBM_INPUT_DIRECTORY=input
```

### Run using streamlit 

from repoistory root

```shell

streamlit run yearlyscurves/scurves_app.py

```

## scurve parameters plot

Plot default scurve parameters. Includes a simple editor.

### Make sure to define EBM_INPUT_DIRECTORY in `.env`

```ini
EBM_INPUT_DIRECTORY=input
```

### Run using streamlit 

from repository root

```shell

streamlit run scurveparams/app.py

```

## construction and demolition bar chart

Bar chart for EBM demolition and construction 

```shell

streamlit run condemo/app.py

```
