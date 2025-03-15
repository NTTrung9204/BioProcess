from config import PostgresConfig

DEFAULT_FIXED_BY_MEAN_VALUE = {
    PostgresConfig.TEM_COL: 298.026658,
    PostgresConfig.DO_COL: 12.571104,
    PostgresConfig.SFR_COL: 76.654912,
    PostgresConfig.ARATE_COL: 65.261404,
    PostgresConfig.WTFD_COL: 154.842992,
    PostgresConfig.VV_COL: 73320.525596,
    PostgresConfig.OUR_COL: 1.258720,
    PostgresConfig.TIME_COL: 114.688522,
}

MIN_VALUES = {
    PostgresConfig.TEM_COL: 296.84,
    PostgresConfig.DO_COL: 1.0,
    PostgresConfig.SFR_COL: 2.0,
    PostgresConfig.ARATE_COL: 20.0,
    PostgresConfig.WTFD_COL: 0.0,
    PostgresConfig.VV_COL: 56549.0,
    PostgresConfig.OUR_COL: -1.242,
    PostgresConfig.TIME_COL: 0.2,
}

MAX_VALUES = {
    PostgresConfig.TEM_COL: 302.18,
    PostgresConfig.DO_COL: 16.508,
    PostgresConfig.SFR_COL: 150.0,
    PostgresConfig.ARATE_COL: 75.0,
    PostgresConfig.WTFD_COL: 500.0,
    PostgresConfig.VV_COL: 95716.0,
    PostgresConfig.OUR_COL: 6.7611,
    PostgresConfig.TIME_COL: 289.8,
}
