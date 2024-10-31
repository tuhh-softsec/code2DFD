from configparser import ConfigParser

code2dfd_config = ConfigParser()

CONFIG_SECTIONS = ["Analysis Settings", "Repository"]
for section in CONFIG_SECTIONS:
    code2dfd_config.add_section(section)
code2dfd_config.set("Analysis Settings", "development_mode", "False")
