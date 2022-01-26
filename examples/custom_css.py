import datetime

import numpy as np
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder


now = int(datetime.datetime.now().timestamp())
start_ts = now - 3 * 30 * 24 * 60 * 60


@st.cache
def make_data():
    df = pd.DataFrame(
        {
            "timestamp": np.random.randint(start_ts, now, 20),
            "side": [np.random.choice(["buy", "sell"]) for i in range(20)],
            "base": [np.random.choice(["JPY", "GBP", "CAD"]) for i in range(20)],
            "quote": [np.random.choice(["EUR", "USD"]) for i in range(20)],
            "amount": list(
                map(
                    lambda a: round(a, 2),
                    np.random.rand(20) * np.random.randint(1, 1000, 20),
                )
            ),
            "price": list(
                map(
                    lambda p: round(p, 5),
                    np.random.rand(20) * np.random.randint(1, 10, 20),
                )
            ),
        }
    )
    df["cost"] = round(df.amount * df.price, 2)
    df.insert(
        0,
        "datetime",
        df.timestamp.apply(lambda ts: datetime.datetime.fromtimestamp(ts)),
    )
    return df.sort_values("timestamp").drop("timestamp", axis=1)


df = make_data()
gb = GridOptionsBuilder.from_dataframe(df)

row_class_rules = {
    "trade-buy-green": "data.side == 'buy'",
    "trade-sell-red": "data.side == 'sell'",
}
gb.configure_grid_options(rowClassRules=row_class_rules)
grid_options = gb.build()

custom_css = {
    ".trade-buy-green": {"color": "green !important"},
    ".trade-sell-red": {"color": "red !important"},
}

st.title("rowClassRules Test")
AgGrid(df, theme="streamlit", custom_css=custom_css, gridOptions=grid_options)

