from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from typer.testing import CliRunner

from archdoc.cli import app
from archdoc.config.loader import load_config


class ConfigInitializerTests(TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_init_creates_a_valid_default_config(self):
        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "archdoc.yml"

            result = self.runner.invoke(app, ["init", "--output", str(destination)])

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue(destination.is_file())
            config = load_config(destination)
            self.assertEqual(config.project.name, "my-python-backend")
            self.assertEqual(config.project.source_root, Path(temp_dir) / "app")

    def test_init_does_not_replace_an_existing_config_without_force(self):
        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "archdoc.yml"
            destination.write_text("existing: true\n", encoding="utf-8")

            result = self.runner.invoke(app, ["init", "--output", str(destination)])

            self.assertEqual(result.exit_code, 1)
            self.assertEqual(destination.read_text(encoding="utf-8"), "existing: true\n")
            self.assertIn("Use --force to replace it", result.output)

    def test_force_replaces_an_existing_config(self):
        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "archdoc.yml"
            destination.write_text("existing: true\n", encoding="utf-8")

            result = self.runner.invoke(
                app,
                ["init", "--output", str(destination), "--force"],
            )

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn("project:", destination.read_text(encoding="utf-8"))

    def test_repository_example_matches_the_packaged_template(self):
        package_root = Path(__file__).resolve().parents[1]
        repository_example = package_root / "archdoc.example.yml"
        packaged_template = (
            package_root / "src" / "archdoc" / "templates" / "archdoc.example.yml"
        )

        self.assertEqual(
            repository_example.read_text(encoding="utf-8"),
            packaged_template.read_text(encoding="utf-8"),
        )
