
import pytest

from configClasses.baseConfig import BaseConfig

test_data = [
    pytest.param("templates/dummy.config"), 
    pytest.param("templates/sqlite_local.config"),
    pytest.param("templates/sqlite_local.json")
]
@pytest.mark.parametrize("config_file_path", test_data)
def test_ini_file_reader(config_file_path):
    """ Testing wrapper function for the config file reader """
    if ".json" in config_file_path:
        config = BaseConfig.read_json_config(config_file_path)
    else:
        config = BaseConfig.read_ini_config(config_file_path)

    assert config.get_attribute("jobdb_dict")
    assert config.get_attribute("compute_dict")
    assert config.get_attribute("transport_dict")

    assert config.get_parameter("jobdb_dict","db_name")


