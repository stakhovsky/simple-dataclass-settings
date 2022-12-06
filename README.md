# simple_dataclass_settings
Simple library on top of dataclasses to create shiny-looking configs from environment variables.

## Example usage
```python3
import simple_dataclass_settings


@simple_dataclass_settings.settings
class SomeChildSettings:
    some_float: float = simple_dataclass_settings.field.float(
        var='SOME_FLOAT',
    )


@simple_dataclass_settings.settings
class Settings:
    some_child: SomeChildSettings
    some_string: str = simple_dataclass_settings.field.str(
        var='SOME_STRING',
        default='test',
    )
    some_number: int = simple_dataclass_settings.field.int(
        var='SOME_NUMBER',
        default=69,
    )
    some_flag: bool = simple_dataclass_settings.field.bool(
        var='SOME_FLAG',
        default=False,
    )
    some_list: bool = simple_dataclass_settings.field.str_list(
        var='SOME_LIST',
        default=['test', 'vars'],
    )


settings = simple_dataclass_settings.populate(Settings)
```

## Interface
 - `settings` - decorator that converts a class to the settings class (just a regular frozen (and slotted) dataclass)
 - `field` - class that creates a special setting field object (that holds metadata about environment variables and its processing)
 - `populate` - function that creates an instance of passed settings class
 - `show` - function that shows a list of environment variables used by the passed class
 - `read_envfile` - function that populates variables from the env file
