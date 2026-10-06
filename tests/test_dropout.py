import pandas as pd
from airsense_r.corruption.dropout import whole_variable_dropout


def test_whole_variable_dropout():
    frame = pd.DataFrame({"NO2": [1.0, 2.0], "CO": [3.0, 4.0]})
    out = whole_variable_dropout(frame, "NO2")
    assert out["NO2"].isna().all()
    assert out["CO"].notna().all()
