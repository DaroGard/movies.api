resource "azurerm_storage_account" "storage" {
  name                     = "storage${var.project}${var.environment}"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.tags
}

resource "azurerm_storage_container" "csv" {
  name                  = "csv-content"
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
}
