resource "azurerm_redis_cache" "redis_cache" {
  name                = "${var.project}rediscacheDB"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name

  capacity            = 0                         
  family              = "C"                       
  sku_name            = "Basic"                  

  tags = var.tags
}