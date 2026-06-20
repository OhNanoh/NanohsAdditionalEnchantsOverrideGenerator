# Nanoh's Additional Enchants Override Generator

A small GUI tool for creating datapack overrides for Nanoh's Additional Enchants.

## Requirements

- Python 3
- Tkinter, included with most standard Python installs on Windows

## Usage

1. Run `nae_override_builder.py`.
2. Choose the enchantments you want to override.
3. Adjust weight, max level, anvil cost, and enchantment cost values.
4. Use Disable to remove an enchantment from supported items.
5. Choose an output folder.
6. Generate the datapack.

For single-player worlds, generate into the world's `datapacks` folder. For servers, generate into the server world's `datapacks` folder, then restart or reload the server.

The tool reads default enchantment data from `nae_enchant_defaults.json`, so keep that file next to the script.
