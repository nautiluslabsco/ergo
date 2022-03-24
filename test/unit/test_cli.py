import tempfile
import yaml
from ergo.ergo_cli import load_config


def test_load_config():
    """
    Assert that namespace files passed to ergo via the command line take precedence over ones that appear in the
    manifest's namespace attribute.
    """
    with tempfile.NamedTemporaryFile(mode="w") as manifest_fh:
        with tempfile.NamedTemporaryFile(mode="w") as default_namespace_fh:
            with tempfile.NamedTemporaryFile(mode="w") as override_namespace_fh:
                default_namespace = {"host": "default_host", "protocol": "default_protocol"}
                override_namespace = {"host": "override_host"}
                manifest = {
                    "namespace": default_namespace_fh.name,
                    "func": "my_handler.py"
                }

                manifest_fh.write(yaml.dump(manifest))
                manifest_fh.seek(0)
                default_namespace_fh.write(yaml.dump(default_namespace))
                default_namespace_fh.seek(0)
                override_namespace_fh.write(yaml.dump(override_namespace))
                override_namespace_fh.seek(0)

                config = load_config(manifest_fh.name, override_namespace_fh.name)

                assert config.func == "my_handler.py"
                assert config.host == "override_host"
                assert config.protocol == "default_protocol"
