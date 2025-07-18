
resource "azurerm_service_plan" "sp" {
    name = "sp-${var.project}-${var.environment}"
    location = "${var.location}"
    resource_group_name = azurerm_resource_group.rg.name
    sku_name = "B1" 
    os_type = "Linux" 
}

resource "azurerm_linux_web_app" "webappui" {
    name = "ui-${var.project}-${var.environment}"
    location = "${var.location}"
    resource_group_name = azurerm_resource_group.rg.name
    service_plan_id = azurerm_service_plan.sp.id
    site_config { 
      always_on = false
      application_stack {
        docker_registry_url = "https://index.docker.io"
        docker_image_name = "nginx:latest"
      }
    }
    app_settings = { 
        WEBSITES_PORT = "80"
    }
}

resource "azurerm_linux_web_app" "webappapi" {
    name = "api-${var.project}-${var.environment}"
    location = "${var.location}"
    resource_group_name = azurerm_resource_group.rg.name
    service_plan_id = azurerm_service_plan.sp.id
    site_config {
      always_on = false
      application_stack {
        docker_registry_url = "https://index.docker.io"
        docker_image_name = "nginx:latest"
      }
    }
    app_settings = {
        WEBSITES_PORT = "80"
    }
}