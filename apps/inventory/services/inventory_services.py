from apps.inventory.models import Inventory, BaseUnit, Presentation

class InventoryService:
    @staticmethod
    def create_inventory_with_config(data):
        option = int(data.get('selected_option', 1))
        inventory = Inventory.objects.create(
            name=data.get('name'),
            description=data.get('description'),
            selected_option=option
        )

        # 1. Configuración de Switches y Catálogos
        if option == 1: # Medicamentos
            inventory.has_concentration = True
            inventory.has_presentation = True
            inventory.has_quantity_per_presentation = True
            inventory.has_expiration_date = True
            
            # Unidades predeterminadas
            units = ['mg', 'ml', 'pastilla']
            # Presentaciones predeterminadas
            pres = ['Tableta', 'Jarabe', 'Intravenoso']
            
        elif option == 2: # Alimentos
            inventory.has_concentration = False
            inventory.has_presentation = True
            inventory.has_quantity_per_presentation = True
            inventory.has_expiration_date = True
            
            units = ['Kg', 'Lb', 'g']
            pres = ['Bolsa', 'Caja', 'Frasco']

        elif option == 3: # Objetos
            inventory.has_concentration = False
            inventory.has_presentation = False
            inventory.has_quantity_per_presentation = False
            inventory.has_expiration_date = False
            
            units = ['unidad'] # Selector con números exactos
            pres = []

        else: # Opción 4: Personalizado
            units, pres = [], []

        # 2. Guardar switches y asociar catálogos
        inventory.save()
        
        for u_name in units:
            unit, _ = BaseUnit.objects.get_or_create(name=u_name)
            inventory.allowed_units.add(unit)
            
        for p_name in pres:
            p_obj, _ = Presentation.objects.get_or_create(name=p_name)
            inventory.allowed_presentations.add(p_obj)

        return inventory

    @staticmethod
    def update_inventory_config(inventory, data):
        """Actualiza la configuración del inventario (Nombre, Switches, Catálogos)."""
        inventory.name = data.get('name', inventory.name)
        inventory.description = data.get('description', inventory.description)
        
        # Actualizar switches
        switches = data.get('switches', {})
        inventory.has_concentration = switches.get('has_concentration', inventory.has_concentration)
        inventory.has_presentation = switches.get('has_presentation', inventory.has_presentation)
        inventory.has_quantity_per_presentation = switches.get('has_quantity_per_presentation', inventory.has_quantity_per_presentation)
        inventory.has_expiration_date = switches.get('has_expiration_date', inventory.has_expiration_date)
        
        inventory.save()
        
        # Actualizar catálogos (Unidades y Presentaciones)
        catalogos = data.get('catalogos', {})
        
        if 'unidades' in catalogos:
            unidades_data = catalogos['unidades'] # Lista de strings
            unit_ids = []
            for u_name in unidades_data:
                unit, _ = BaseUnit.objects.get_or_create(name=u_name)
                unit_ids.append(unit.id)
            inventory.allowed_units.set(unit_ids)
            
        if 'presentaciones' in catalogos:
            pres_data = catalogos['presentaciones'] # Lista de strings
            pres_ids = []
            for p_name in pres_data:
                p_obj, _ = Presentation.objects.get_or_create(name=p_name)
                pres_ids.append(p_obj.id)
            inventory.allowed_presentations.set(pres_ids)
            
        return inventory