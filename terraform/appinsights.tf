resource "azurerm_application_insights" "app_insights" {
    name = "appi-${var.project}-${var.environment}"
    location = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
    application_type = "web"

    tags = var.tags
}