# %%
%reload_ext autoreload
%autoreload 2
#%%
from timeit import timeit
import pandas as pd
import numpy as np
from itertools import cycle
from st_aggrid import _cast_tz_aware_date_columns_to_iso8601, _get_row_data
# %%
def generate_data(samples):
    deltas = cycle([
            pd.Timedelta(weeks=-2),
            pd.Timedelta(days=-1),
            pd.Timedelta(hours=-1),
            pd.Timedelta(0),
            pd.Timedelta(minutes=5),
            pd.Timedelta(seconds=10),
            pd.Timedelta(microseconds=50),
            pd.Timedelta(microseconds=10)
            ])
    dummy_data = {
        "date_time_naive":[next(cycle(pd.date_range('2021-01-01', periods=36))) for i in range(samples)],
        "apple":np.random.randint(0,100,samples) / 3.0,
        "banana":np.random.randint(0,100,samples) / 5.0,
        "chocolate":np.random.randint(0,100,samples),
        "group": np.random.choice(['A','B'], size=samples),
        "date_only":[next(cycle(pd.date_range('2020-01-01', periods=36).date)) for i in range(samples)],
        "timedelta":[next(deltas) for i in range(samples)],
        "date_tz_aware":[next(cycle(pd.date_range('2022-01-01', periods=36, tz="Asia/Katmandu"))) for i in range(samples)]
    }
    return pd.DataFrame(dummy_data)
df = generate_data(100)
# %%
df = pd.concat([df] * 10000)
# %%timeit
x = _cast_tz_aware_date_columns_to_iso8601(df)
x.to_json(orient='records')
# %%
_get_row_data(df)
# %%
