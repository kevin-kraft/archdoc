from pathlib import Path

import typer

from archdoc.config.loader import load_config
from archdoc.facts.loader import load_raw_facts
from archdoc.facts.writer import write_raw_facts
from archdoc.catalog.writer import (
    write_action_catalog,
    write_endpoint_catalog, 
    write_service_catalog,
    write_endpoint_service_links,
    write_operation_link_catalog,
)
from archdoc.catalog.id_resolver import (
    resolve_catalog_id_collisions,
    resolve_link_id_collisions,
)
from archdoc.mapper.endpoint_mapper import map_endpoints
from archdoc.mapper.service_mapper import map_services
from archdoc.mapper.action_mapper import map_actions
from archdoc.mapper.operation_link_mapper import map_operation_links
from archdoc.scanner.python_scanner import scan_project
from archdoc.linker.endpoint_service_linker import link_endpoints_to_services
from archdoc.linker.mark_linked_endpoint_implementations import mark_linked_endpoint_implementations
from archdoc.validator.catalog_validator import validate_catalog
from archdoc.validator.writer import write_validation_report
from archdoc.exporter.docusaurus_exporter import export_docusaurus_data
from archdoc.schema_exporter import export_json_schemas

app = typer.Typer(
    help="archdoc - deterministic architecture documentation tooling"
)


@app.callback()
def main():
    pass


@app.command()
def scan(config: Path = typer.Option(..., "--config", "-c")):
    cfg = load_config(config)

    facts = scan_project(cfg)
    write_raw_facts(facts, cfg.output.raw_facts)

    total_classes = sum(len(file.classes) for file in facts.files)
    total_methods = sum(len(cls.methods) for file in facts.files for cls in file.classes)
    total_functions = sum(len(file.functions) for file in facts.files)
    total_calls = (
        sum(len(fn.calls) for file in facts.files for fn in file.functions)
        + sum(len(method.calls) for file in facts.files for cls in file.classes for method in cls.methods)
    )
    top_level_calls = sum(
        1
        for file in facts.files
        for fn in file.functions
        for call in fn.calls
        if not call.nested_in_call
    ) + sum(
        1
        for file in facts.files
        for cls in file.classes
        for method in cls.methods
        for call in method.calls
        if not call.nested_in_call
    )

    total_routes = sum(
        1
        for file in facts.files
        for fn in file.functions
        for signal in fn.signals
        if signal.kind == "api_route"
    )

    total_service_candidates = sum(
        1
        for file in facts.files
        for cls in file.classes
        for signal in cls.signals
        if signal.kind == "class_name_suffix" and signal.data.get("suffix") == "Service"
    )

    typer.echo(f"Scanned files: {len(facts.files)}")
    typer.echo(f"Classes: {total_classes}")
    typer.echo(f"Methods: {total_methods}")
    typer.echo(f"Functions: {total_functions}")
    typer.echo(f"Calls: {total_calls}")
    typer.echo(f"Top Level Calls: {top_level_calls}")
    typer.echo(f"API routes: {total_routes}")
    typer.echo(f"Service candidates: {total_service_candidates}")
    typer.echo(f"Wrote raw facts to: {cfg.output.raw_facts}")


@app.command()
def map(config: Path = typer.Option(..., "--config", "-c")):
    cfg = load_config(config)

    if cfg.output.catalog_dir is None:
        raise typer.BadParameter("output.catalog_dir is required for map command")

    facts = load_raw_facts(cfg.output.raw_facts)

    services = map_services(facts, cfg)
    endpoints = map_endpoints(facts, cfg)
    services, endpoints = resolve_catalog_id_collisions(services, endpoints)

    links = link_endpoints_to_services(
        facts=facts,
        endpoints=endpoints,
        services=services,
    )
    links = resolve_link_id_collisions(links)

    endpoints = mark_linked_endpoint_implementations(endpoints, links)
    actions = map_actions(
        facts=facts,
        config=cfg,
        services=services,
        endpoints=endpoints,
    )
    operation_links = map_operation_links(
        facts=facts,
        config=cfg,
        services=services,
    )

    write_service_catalog(
        services=services,
        catalog_dir=cfg.output.catalog_dir,
    )

    write_endpoint_catalog(
        endpoints=endpoints,
        catalog_dir=cfg.output.catalog_dir,
    )

    write_endpoint_service_links(
        links=links,
        catalog_dir=cfg.output.catalog_dir,
    )

    write_action_catalog(
        actions=actions,
        catalog_dir=cfg.output.catalog_dir,
    )

    write_operation_link_catalog(
        operation_links=operation_links,
        catalog_dir=cfg.output.catalog_dir,
    )

    report = validate_catalog(
        facts=facts,
        services=services,
        endpoints=endpoints,
        links=links,
    )

    write_validation_report(
        report=report,
        catalog_dir=cfg.output.catalog_dir,
    )
    

    operation_count = sum(len(service.operations) for service in services)
    linked_endpoint_count = len({link.endpoint_id for link in links})

    if cfg.output.docusaurus_static_dir is not None:
        export_docusaurus_data(
            services=services,
            endpoints=endpoints,
            links=links,
            validation_report=report,
            output_dir=cfg.output.docusaurus_static_dir,
            actions=actions,
            operation_links=operation_links,
        )

   

    typer.echo(f"Mapped services: {len(services)}")
    typer.echo(f"Mapped operations: {operation_count}")
    typer.echo(f"Mapped endpoints: {len(endpoints)}")
    typer.echo(f"Wrote service catalog to: {cfg.output.catalog_dir / 'services'}")
    typer.echo(f"Wrote endpoint catalog to: {cfg.output.catalog_dir / 'endpoints'}")
    
    typer.echo(f"Linked endpoint-service calls: {len(links)}")
    typer.echo(f"Endpoints with service links: {linked_endpoint_count}/{len(endpoints)}")
    typer.echo(f"Mapped architecture actions: {len(actions)}")
    typer.echo(f"Mapped operation links: {len(operation_links)}")

    typer.echo(f"Validation errors: {report.summary.errors}")
    typer.echo(f"Validation warnings: {report.summary.warnings}")
    typer.echo(f"Validation infos: {report.summary.infos}")
    typer.echo(f"Wrote validation report to: {cfg.output.catalog_dir / 'reports' / 'validation_report.json'}")
    
    typer.echo(f"Wrote Docusaurus data to: {cfg.output.docusaurus_static_dir}")


@app.command("export-schemas")
def export_schemas(config: Path = typer.Option(..., "--config", "-c")):
    cfg = load_config(config)

    if cfg.output.schema_dir is None:
        raise typer.BadParameter("output.schema_dir is required for export-schemas command")

    written_paths = export_json_schemas(cfg.output.schema_dir)

    typer.echo(f"Exported JSON schemas: {len(written_paths)}")
    typer.echo(f"Wrote JSON schemas to: {cfg.output.schema_dir}")

    for path in written_paths:
        typer.echo(f"- {path.name}")


if __name__ == "__main__":
    app()
