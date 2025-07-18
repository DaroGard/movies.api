resource "azurerm_mssql_server" "sqlserver" {
  name                         = "sqlserver-${var.project}-${var.environment}"
  resource_group_name          = azurerm_resource_group.rg.name
  location                     = azurerm_resource_group.rg.location
  version                      = "12.0"
  administrator_login          = var.admin_sql_user
  administrator_login_password = var.admin_sql_password
}

resource "azurerm_mssql_database" "moviesdb" {
  name      = "db${var.project}"
  server_id = azurerm_mssql_server.sqlserver.id
  sku_name  = "S0"
}