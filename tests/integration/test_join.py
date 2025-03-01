import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal


def test_join(c):
    df = c.sql(
        "SELECT lhs.user_id, lhs.b, rhs.c FROM user_table_1 AS lhs JOIN user_table_2 AS rhs ON lhs.user_id = rhs.user_id"
    )
    df = df.compute()

    expected_df = pd.DataFrame(
        {"user_id": [1, 1, 2, 2], "b": [3, 3, 1, 3], "c": [1, 2, 3, 3]}
    )
    assert_frame_equal(
        df.sort_values(["user_id", "b", "c"]).reset_index(drop=True), expected_df,
    )


def test_join_inner(c):
    df = c.sql(
        "SELECT lhs.user_id, lhs.b, rhs.c FROM user_table_1 AS lhs INNER JOIN user_table_2 AS rhs ON lhs.user_id = rhs.user_id"
    )
    df = df.compute()

    expected_df = pd.DataFrame(
        {"user_id": [1, 1, 2, 2], "b": [3, 3, 1, 3], "c": [1, 2, 3, 3]}
    )
    assert_frame_equal(
        df.sort_values(["user_id", "b", "c"]).reset_index(drop=True), expected_df,
    )


def test_join_outer(c):
    df = c.sql(
        "SELECT lhs.user_id, lhs.b, rhs.c FROM user_table_1 AS lhs FULL JOIN user_table_2 AS rhs ON lhs.user_id = rhs.user_id"
    )
    df = df.compute()

    expected_df = pd.DataFrame(
        {
            # That is strange. Unfortunately, it seems dask fills in the
            # missing rows with NaN, not with NA...
            "user_id": [1, 1, 2, 2, 3, np.NaN],
            "b": [3, 3, 1, 3, 3, np.NaN],
            "c": [1, 2, 3, 3, np.NaN, 4],
        }
    )
    assert_frame_equal(
        df.sort_values(["user_id", "b", "c"]).reset_index(drop=True), expected_df
    )


def test_join_left(c):
    df = c.sql(
        "SELECT lhs.user_id, lhs.b, rhs.c FROM user_table_1 AS lhs LEFT JOIN user_table_2 AS rhs ON lhs.user_id = rhs.user_id"
    )
    df = df.compute()

    expected_df = pd.DataFrame(
        {
            # That is strange. Unfortunately, it seems dask fills in the
            # missing rows with NaN, not with NA...
            "user_id": [1, 1, 2, 2, 3],
            "b": [3, 3, 1, 3, 3],
            "c": [1, 2, 3, 3, np.NaN],
        }
    )
    assert_frame_equal(
        df.sort_values(["user_id", "b", "c"]).reset_index(drop=True), expected_df,
    )


def test_join_right(c):
    df = c.sql(
        "SELECT lhs.user_id, lhs.b, rhs.c FROM user_table_1 AS lhs RIGHT JOIN user_table_2 AS rhs ON lhs.user_id = rhs.user_id"
    )
    df = df.compute()

    expected_df = pd.DataFrame(
        {
            # That is strange. Unfortunately, it seems dask fills in the
            # missing rows with NaN, not with NA...
            "user_id": [1, 1, 2, 2, np.NaN],
            "b": [3, 3, 1, 3, np.NaN],
            "c": [1, 2, 3, 3, 4],
        }
    )
    assert_frame_equal(
        df.sort_values(["user_id", "b", "c"]).reset_index(drop=True), expected_df,
    )


def test_join_complex(c):
    df = c.sql(
        "SELECT lhs.a, rhs.b FROM df_simple AS lhs JOIN df_simple AS rhs ON lhs.a < rhs.b",
    )
    df = df.compute()

    df_expected = pd.DataFrame(
        {"a": [1, 1, 1, 2, 2, 3], "b": [1.1, 2.2, 3.3, 2.2, 3.3, 3.3]}
    )

    assert_frame_equal(df.sort_values(["a", "b"]).reset_index(drop=True), df_expected)

    df = c.sql(
        """
            SELECT lhs.a, lhs.b, rhs.a, rhs.b
            FROM
                df_simple AS lhs
            JOIN df_simple AS rhs
            ON lhs.a < rhs.b AND lhs.b < rhs.a
        """
    )
    df = df.compute()

    df_expected = pd.DataFrame(
        {"a": [1, 1, 2], "b": [1.1, 1.1, 2.2], "a0": [2, 3, 3], "b0": [2.2, 3.3, 3.3],}
    )

    assert_frame_equal(df.sort_values(["a", "b0"]).reset_index(drop=True), df_expected)


def test_join_complex_2(c):
    df = c.sql(
        """
    SELECT
        lhs.user_id, lhs.b, rhs.user_id, rhs.c
    FROM user_table_1 AS lhs
    JOIN user_table_2 AS rhs
        ON rhs.user_id = lhs.user_id AND rhs.c - lhs.b >= 0
    """
    )

    df = df.compute()

    df_expected = pd.DataFrame(
        {"user_id": [2, 2], "b": [1, 3], "user_id0": [2, 2], "c": [3, 3]}
    )

    assert_frame_equal(df.sort_values("b").reset_index(drop=True), df_expected)


def test_join_literal(c):
    df = c.sql(
        """
    SELECT
        lhs.user_id, lhs.b, rhs.user_id, rhs.c
    FROM user_table_1 AS lhs
    JOIN user_table_2 AS rhs
        ON True
    """
    )

    df = df.compute()

    df_expected = pd.DataFrame(
        {
            "user_id": [2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3],
            "b": [1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
            "user_id0": [1, 1, 2, 4, 1, 1, 2, 4, 1, 1, 2, 4, 1, 1, 2, 4],
            "c": [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
        }
    )

    assert_frame_equal(
        df.sort_values(["b", "user_id", "user_id0"]).reset_index(drop=True),
        df_expected,
    )

    df = c.sql(
        """
    SELECT
        lhs.user_id, lhs.b, rhs.user_id, rhs.c
    FROM user_table_1 AS lhs
    JOIN user_table_2 AS rhs
        ON False
    """
    )

    df = df.compute()

    df_expected = pd.DataFrame({"user_id": [], "b": [], "user_id0": [], "c": []})

    assert_frame_equal(df.reset_index(), df_expected.reset_index(), check_dtype=False)


def test_join_lricomplex(c):
    # ---------- Panel data (equality and inequality conditions)

    # Correct answer
    dfcorrpn = pd.DataFrame(
        [
            [0, 1, pd.NA, pd.NA, pd.NA, pd.NA],
            [1, 5, 32, 2, pd.NA, 112],
            [1, 5, 32, 4, 13, 113],
            [2, 1, 33, pd.NA, pd.NA, pd.NA],
        ],
        columns=["ids", "dates", "pn_nullint", "startdate", "lk_nullint", "lk_int",],
    )
    change_types = {
        "pn_nullint": "Int32",
        "lk_nullint": "Int32",
        "startdate": "Int64",
        "lk_int": "Int64",
    }
    for k, v in change_types.items():
        dfcorrpn[k] = dfcorrpn[k].astype(v)

    # Left Join
    querypnl = """
        select a.*, b.startdate, b.lk_nullint, b.lk_int
        from user_table_pn a left join user_table_lk b
        on a.ids=b.id and b.startdate<=a.dates
        """
    dftestpnl = (
        c.sql(querypnl)
        .compute()
        .sort_values(["ids", "dates", "startdate"])
        .reset_index(drop=True)
    )
    assert_frame_equal(dftestpnl, dfcorrpn, check_dtype=False)

    # Right Join
    querypnr = """
        select b.*, a.startdate, a.lk_nullint, a.lk_int
        from user_table_lk a right join user_table_pn b
        on b.ids=a.id and a.startdate<=b.dates
        """
    dftestpnr = (
        c.sql(querypnr)
        .compute()
        .sort_values(["ids", "dates", "startdate"])
        .reset_index(drop=True)
    )
    assert_frame_equal(dftestpnr, dfcorrpn, check_dtype=False)

    # Inner Join
    querypni = """
        select a.*, b.startdate, b.lk_nullint, b.lk_int
        from user_table_pn a inner join user_table_lk b
        on a.ids=b.id and b.startdate<=a.dates
        """
    dftestpni = (
        c.sql(querypni)
        .compute()
        .sort_values(["ids", "dates", "startdate"])
        .reset_index(drop=True)
    )
    assert_frame_equal(
        dftestpni,
        dfcorrpn.dropna(subset=["startdate"])
        .assign(
            startdate=lambda x: x["startdate"].astype("int64"),
            lk_int=lambda x: x["lk_int"].astype("int64"),
        )
        .reset_index(drop=True),
        check_dtype=False,
    )

    # ---------- Time-series data (inequality condition only)

    # # Correct answer
    dfcorrts = pd.DataFrame(
        [
            [1, 21, pd.NA, pd.NA, pd.NA],
            [3, pd.NA, 2, pd.NA, 112],
            [7, 23, 2, pd.NA, 112],
            [7, 23, 4, 13, 113],
        ],
        columns=["dates", "ts_nullint", "startdate", "lk_nullint", "lk_int",],
    )
    change_types = {
        "ts_nullint": "Int32",
        "lk_nullint": "Int32",
        "startdate": "Int64",
        "lk_int": "Int64",
    }
    for k, v in change_types.items():
        dfcorrts[k] = dfcorrts[k].astype(v)

    # Left Join
    querytsl = """
        select a.*, b.startdate, b.lk_nullint, b.lk_int
        from user_table_ts a left join user_table_lk2 b
        on b.startdate<=a.dates
    """
    dftesttsl = (
        c.sql(querytsl)
        .compute()
        .sort_values(["dates", "startdate"])
        .reset_index(drop=True)
    )
    assert_frame_equal(dftesttsl, dfcorrts, check_dtype=False)

    # Right Join
    querytsr = """
        select b.*, a.startdate, a.lk_nullint, a.lk_int
        from user_table_lk2 a right join user_table_ts b
        on a.startdate<=b.dates
    """
    dftesttsr = (
        c.sql(querytsr)
        .compute()
        .sort_values(["dates", "startdate"])
        .reset_index(drop=True)
    )
    assert_frame_equal(dftesttsr, dfcorrts, check_dtype=False)

    # Inner Join
    querytsi = """
        select a.*, b.startdate, b.lk_nullint, b.lk_int
        from user_table_ts a inner join user_table_lk2 b
        on b.startdate<=a.dates
    """
    dftesttsi = (
        c.sql(querytsi)
        .compute()
        .sort_values(["dates", "startdate"])
        .reset_index(drop=True)
    )
    assert_frame_equal(
        dftesttsi,
        dfcorrts.dropna(subset=["startdate"])
        .assign(
            startdate=lambda x: x["startdate"].astype("int64"),
            lk_int=lambda x: x["lk_int"].astype("int64"),
        )
        .reset_index(drop=True),
        check_dtype=False,
    )
