from archdoc.catalog.models import EndpointCatalogItem, EndpointServiceLinkItem, EndpointImplementation, EndpointImplementationKind, DetectionConfidence


def mark_linked_endpoint_implementations(
    endpoints: list[EndpointCatalogItem],
    links: list[EndpointServiceLinkItem],
) -> list[EndpointCatalogItem]:
    linked_endpoint_ids = {link.endpoint_id for link in links}

    updated: list[EndpointCatalogItem] = []

    for endpoint in endpoints:
        if endpoint.id not in linked_endpoint_ids:
            updated.append(endpoint)
            continue

        endpoint.implementation = EndpointImplementation(
            kind=EndpointImplementationKind.SERVICE_OPERATION,
            confidence=DetectionConfidence.HIGH,
            reason="Endpoint was linked to at least one service operation.",
            signals=[
                *endpoint.implementation.signals,
                "endpoint_service_link_resolved",
            ],
        )

        updated.append(endpoint)

    return updated