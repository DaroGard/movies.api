resource "azurerm_container_registry" "movies_acr" {
  name                = "moviesacr${var.project}"  
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = true
  
  tags = var.tags
  
}