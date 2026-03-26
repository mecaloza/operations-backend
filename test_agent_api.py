#!/usr/bin/env python3
"""
Script de testing para Agent API
Uso: python3 test_agent_api.py
"""
import requests
import json

# Configuración
API_BASE = "https://ops-backend-production-e8ce.up.railway.app/api/v1"
# API_BASE = "http://localhost:8000/api/v1"  # Para testing local

# Primero necesitas obtener tu API key desde la DB o registrar un nuevo agente
# Este es un ejemplo con el agente Shosanna


def test_register_agent():
    """Test: Registrar nuevo agente"""
    print("\n🔐 Test: Registrar nuevo agente")
    print("=" * 60)
    
    response = requests.post(
        f"{API_BASE}/agent-api/auth/register",
        json={
            "agent_name": "TestAgent 🤖",
            "permissions": "read:tasks,write:tasks,read:projects,read:epics"
        }
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Agente registrado exitosamente!")
        print(f"API Key: {data['api_key']}")
        print(f"Guardar este API key para los siguientes tests")
        return data['api_key']
    else:
        print(f"❌ Error: {response.json()}")
        return None


def test_auth_test(api_key: str):
    """Test: Verificar autenticación"""
    print("\n🔐 Test: Verificar autenticación")
    print("=" * 60)
    
    headers = {"X-Agent-API-Key": api_key}
    response = requests.get(f"{API_BASE}/agent-api/auth/test", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Autenticado como: {data['agent_name']}")
        print(f"Permisos: {', '.join(data['permissions'])}")
        print(f"Rate limit: {data['rate_limit']} req/min")
        print(f"Último acceso: {data['last_access']}")
    else:
        print(f"❌ Error: {response.json()}")


def test_get_assigned_tasks(api_key: str):
    """Test: Obtener tareas asignadas"""
    print("\n📋 Test: Obtener tareas asignadas")
    print("=" * 60)
    
    headers = {"X-Agent-API-Key": api_key}
    response = requests.get(
        f"{API_BASE}/agent-api/tasks/assigned",
        headers=headers,
        params={"status": "in_progress"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        tasks = response.json()
        print(f"✅ {len(tasks)} tareas encontradas")
        for task in tasks[:3]:  # Mostrar primeras 3
            print(f"\n  Task #{task['id']}: {task['title']}")
            print(f"  Status: {task['status']} | Priority: {task['priority']}")
            print(f"  Assigned to: {task['assigned_to']}")
    else:
        print(f"❌ Error: {response.json()}")


def test_get_projects(api_key: str):
    """Test: Obtener proyectos"""
    print("\n🗂️  Test: Obtener proyectos")
    print("=" * 60)
    
    headers = {"X-Agent-API-Key": api_key}
    response = requests.get(f"{API_BASE}/agent-api/projects", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        projects = response.json()
        print(f"✅ {len(projects)} proyectos encontrados")
        for proj in projects:
            print(f"\n  Project #{proj['id']}: {proj['name']}")
            print(f"  Slug: {proj['slug']} | Status: {proj['status']}")
    else:
        print(f"❌ Error: {response.json()}")


def test_update_task_status(api_key: str, task_id: int):
    """Test: Actualizar estado de tarea"""
    print(f"\n✏️  Test: Actualizar estado de tarea #{task_id}")
    print("=" * 60)
    
    headers = {"X-Agent-API-Key": api_key}
    response = requests.patch(
        f"{API_BASE}/agent-api/tasks/{task_id}/status",
        headers=headers,
        json={"status": "done"}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        task = response.json()
        print(f"✅ Tarea actualizada!")
        print(f"Task #{task['id']}: {task['title']}")
        print(f"Nuevo status: {task['status']}")
    else:
        print(f"❌ Error: {response.json()}")


def test_rate_limiting(api_key: str):
    """Test: Rate limiting"""
    print("\n⏱️  Test: Rate limiting (enviando 65 requests)")
    print("=" * 60)
    
    headers = {"X-Agent-API-Key": api_key}
    success_count = 0
    rate_limited_count = 0
    
    for i in range(65):
        response = requests.get(f"{API_BASE}/agent-api/auth/test", headers=headers)
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
            if rate_limited_count == 1:
                print(f"\n❌ Rate limit alcanzado después de {success_count} requests")
                print(f"Mensaje: {response.json()['detail']}")
                break
    
    print(f"\n✅ Requests exitosos: {success_count}")
    print(f"⛔ Requests bloqueados: {rate_limited_count}")


def main():
    """Ejecutar todos los tests"""
    print("\n" + "=" * 60)
    print("🤖 Testing Agent API - Operations Dashboard")
    print("=" * 60)
    
    # Opción 1: Registrar nuevo agente
    print("\n¿Quieres registrar un nuevo agente de prueba? (y/n)")
    choice = input("> ").lower().strip()
    
    if choice == "y":
        api_key = test_register_agent()
        if not api_key:
            print("\n❌ No se pudo registrar el agente. Abortando.")
            return
    else:
        # Opción 2: Usar API key existente
        print("\nIngresa tu API key:")
        api_key = input("> ").strip()
    
    # Ejecutar tests
    test_auth_test(api_key)
    test_get_assigned_tasks(api_key)
    test_get_projects(api_key)
    
    # Test de actualización de tarea (opcional)
    print("\n¿Quieres probar actualizar una tarea? Ingresa el task_id o 'n' para omitir:")
    task_id_input = input("> ").strip()
    if task_id_input.isdigit():
        test_update_task_status(api_key, int(task_id_input))
    
    # Test de rate limiting (opcional)
    print("\n¿Quieres probar el rate limiting? (y/n)")
    choice = input("> ").lower().strip()
    if choice == "y":
        test_rate_limiting(api_key)
    
    print("\n" + "=" * 60)
    print("✅ Tests completados")
    print("=" * 60)


if __name__ == "__main__":
    main()
