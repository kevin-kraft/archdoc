@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    org_id: str = Depends(require_org_context),
    user: Any = Depends(get_current_user),
    _: None = Depends(require_permission(PaymentPermissions.PROVIDER_MANAGE)),
): 

- Verbesserung Trace der Route in User Stories: 
    - eine Darstellung von Permissions in User Stories, mit endpoints die keine Service Verbindung haben 
    - bessere Darstellung von Informationen im Trace
        - Schlecht: Types werden einfach hintereinander angezeigt sowie Endpoints ==> Sortieren, Besseren Graphen darstellen vielleicht (eher vie in service action graph aber fokusiert) 