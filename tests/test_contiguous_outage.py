import pandas as pd

from airsense_r.corruption.dropout import contiguous_outage


def test_contiguous_outage_changes_only_requested_interval_and_columns():
    frame = pd.DataFrame({"sensor": range(8), "target": range(100, 108)})
    out = contiguous_outage(frame, ["sensor"], start=2, length=3)
    assert out.loc[2:4, "sensor"].isna().all()
    assert out.loc[:1, "sensor"].notna().all()
    assert out.loc[5:, "sensor"].notna().all()
    assert out["target"].equals(frame["target"])
