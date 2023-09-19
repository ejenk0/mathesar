import pytest
import uuid

from mathesar.models.shares import SharedTable


@pytest.fixture
def schemas_with_shared_tables(create_patents_table, uid):
    table_name = f"schemas_with_shared_tables_{uid}"
    table = create_patents_table(table_name)
    share = SharedTable.objects.create(
        table=table,
        enabled=True,
    )
    different_schema_table = create_patents_table(table_name, schema_name="Different Schema")
    different_schema_share = SharedTable.objects.create(
        table=different_schema_table,
        enabled=True,
    )
    yield {
        'patents_schema': table.schema,
        'patents_table': table,
        'patents_table_share': share,
        'different_schema': different_schema_table.schema,
        'different_schema_table': different_schema_table,
        'different_schema_table_share': different_schema_share,
    }
    share.delete()
    table.delete()
    different_schema_share.delete()
    different_schema_table.delete()


read_client_with_different_roles = [
    # (client_name, different_schema_status_code)
    ('superuser_client_factory', 200),
    ('db_manager_client_factory', 200),
    ('db_editor_client_factory', 200),
    ('schema_manager_client_factory', 403),
    ('schema_viewer_client_factory', 403),
    ('db_viewer_schema_manager_client_factory', 200)
]


write_client_with_different_roles = [
    # client_name, is_allowed
    ('superuser_client_factory', True),
    ('db_manager_client_factory', True),
    ('db_editor_client_factory', True),
    ('schema_manager_client_factory', True),
    ('schema_viewer_client_factory', False),
    ('db_viewer_schema_manager_client_factory', True)
]


@pytest.mark.parametrize('client_name,different_schema_status_code', read_client_with_different_roles)
def test_shared_table_list(
    schemas_with_shared_tables,
    request,
    client_name,
    different_schema_status_code,
):
    client = request.getfixturevalue(client_name)(schemas_with_shared_tables["patents_schema"])
    response = client.get(f'/api/ui/v0/tables/{schemas_with_shared_tables["patents_table"].id}/shares/')
    response_data = response.json()

    assert response.status_code == 200
    assert response_data['count'] == 1
    assert len(response_data['results']) == 1
    result = response_data['results'][0]
    assert result['slug'] == str(schemas_with_shared_tables['patents_table_share'].slug)
    assert result['enabled'] == schemas_with_shared_tables['patents_table_share'].enabled

    response = client.get(f'/api/ui/v0/tables/{schemas_with_shared_tables["different_schema_table"].id}/shares/')
    assert response.status_code == different_schema_status_code
    if different_schema_status_code == 200:
        response_data = response.json()
        assert len(response_data['results']) == 1
        result = response_data['results'][0]
        assert result['slug'] == str(schemas_with_shared_tables['different_schema_table_share'].slug)
        assert result['enabled'] == schemas_with_shared_tables['different_schema_table_share'].enabled


@pytest.mark.parametrize('client_name,different_schema_status_code', read_client_with_different_roles)
def test_shared_table_retrieve(
    schemas_with_shared_tables,
    request,
    client_name,
    different_schema_status_code,
):
    client = request.getfixturevalue(client_name)(schemas_with_shared_tables["patents_schema"])
    response = client.get(f'/api/ui/v0/tables/{schemas_with_shared_tables["patents_table"].id}/shares/{schemas_with_shared_tables["patents_table_share"].id}/')
    response_data = response.json()

    assert response.status_code == 200
    assert response_data['slug'] == str(schemas_with_shared_tables['patents_table_share'].slug)
    assert response_data['enabled'] == schemas_with_shared_tables['patents_table_share'].enabled

    response = client.get(f'/api/ui/v0/tables/{schemas_with_shared_tables["different_schema_table"].id}/shares/{schemas_with_shared_tables["different_schema_table_share"].id}/')
    assert response.status_code == different_schema_status_code
    if different_schema_status_code == 200:
        response_data = response.json()
        assert response_data['slug'] == str(schemas_with_shared_tables['different_schema_table_share'].slug)
        assert response_data['enabled'] == schemas_with_shared_tables['different_schema_table_share'].enabled


@pytest.mark.parametrize('client_name,is_allowed', write_client_with_different_roles)
def test_shared_table_create(
    patents_table,
    request,
    client_name,
    is_allowed
):
    client = request.getfixturevalue(client_name)(patents_table.schema)
    data = {'enabled': True}
    response = client.post(f'/api/ui/v0/tables/{patents_table.id}/shares/', data)
    response_data = response.json()

    if is_allowed:
        assert response.status_code == 201
        assert 'id' in response_data
        assert response_data['enabled'] is True
        created_share = SharedTable.objects.get(id=response_data['id'])
        assert created_share is not None
    else:
        assert response.status_code == 403

    # clean up
    patents_table.delete()


@pytest.mark.parametrize('client_name,is_allowed', write_client_with_different_roles)
def test_shared_table_patch(
    schemas_with_shared_tables,
    request,
    client_name,
    is_allowed
):
    client = request.getfixturevalue(client_name)(schemas_with_shared_tables["patents_schema"])
    data = {'enabled': False}
    response = client.patch(f'/api/ui/v0/tables/{schemas_with_shared_tables["patents_table"].id}/shares/{schemas_with_shared_tables["patents_table_share"].id}/', data)
    response_data = response.json()

    if is_allowed:
        assert response.status_code == 200
        assert response_data['slug'] == str(schemas_with_shared_tables['patents_table_share'].slug)
        assert response_data['enabled'] is False
    else:
        assert response.status_code == 403


@pytest.mark.parametrize('client_name,is_allowed', write_client_with_different_roles)
def test_shared_table_delete(
    schemas_with_shared_tables,
    request,
    client_name,
    is_allowed
):
    client = request.getfixturevalue(client_name)(schemas_with_shared_tables["patents_schema"])
    response = client.delete(f'/api/ui/v0/tables/{schemas_with_shared_tables["patents_table"].id}/shares/{schemas_with_shared_tables["patents_table_share"].id}/')

    if is_allowed:
        assert response.status_code == 204
        assert SharedTable.objects.filter(id=schemas_with_shared_tables['patents_table_share'].id).first() is None
    else:
        assert response.status_code == 403


@pytest.mark.parametrize('client_name,is_allowed', write_client_with_different_roles)
def test_shared_table_regenerate_link(
    schemas_with_shared_tables,
    request,
    client_name,
    is_allowed
):
    client = request.getfixturevalue(client_name)(schemas_with_shared_tables["patents_schema"])
    old_slug = str(schemas_with_shared_tables["patents_table_share"].slug)
    response = client.post(f'/api/ui/v0/tables/{schemas_with_shared_tables["patents_table"].id}/shares/{schemas_with_shared_tables["patents_table_share"].id}/regenerate/')
    response_data = response.json()

    if is_allowed:
        assert response.status_code == 200
        assert response_data['slug'] != old_slug
    else:
        assert response.status_code == 403


# Table endpoints with share-link-uuid token

tables_request_client_with_different_roles = [
    # (client_name, same_schema_invalid_token_status, different_schema_invalid_token_status)
    ('superuser_client_factory', 200, 200),
    ('db_manager_client_factory', 200, 200),
    ('db_editor_client_factory', 200, 200),
    ('schema_manager_client_factory', 200, 403),
    ('schema_viewer_client_factory', 200, 403),
    ('db_viewer_schema_manager_client_factory', 200, 200),
    ('anonymous_client_factory', 401, 401)
]


@pytest.mark.parametrize('client_name,same_schema_invalid_token_status,different_schema_invalid_token_status', tables_request_client_with_different_roles)
@pytest.mark.parametrize('endpoint', ['columns', 'constraints', 'records'])
def test_shared_table_view_requests(
    schemas_with_shared_tables,
    request,
    endpoint,
    client_name,
    same_schema_invalid_token_status,
    different_schema_invalid_token_status
):
    client = request.getfixturevalue(client_name)(schemas_with_shared_tables["patents_schema"])

    table_url = f'/api/db/v0/tables/{schemas_with_shared_tables["patents_table"].id}'
    share_uuid_param = f'shared-link-uuid={schemas_with_shared_tables["patents_table_share"].slug}'
    invalid_share_uuid_param = f'shared-link-uuid={uuid.uuid4()}'
    different_schema_table_url = f'/api/db/v0/tables/{schemas_with_shared_tables["different_schema_table"].id}'
    different_schema_table_uuid_param = f'shared-link-uuid={schemas_with_shared_tables["different_schema_table_share"].slug}'

    response = client.get(f'{table_url}/{endpoint}/?{share_uuid_param}')
    response_data = response.json()
    assert response.status_code == 200
    assert len(response_data['results']) >= 1

    response = client.get(f'{table_url}/{endpoint}/?{invalid_share_uuid_param}')
    response_data = response.json()
    assert response.status_code == same_schema_invalid_token_status
    if same_schema_invalid_token_status == 200:
        assert len(response_data['results']) >= 1

    response = client.get(f'{different_schema_table_url}/{endpoint}/?{different_schema_table_uuid_param}')
    response_data = response.json()
    assert response.status_code == 200
    assert len(response_data['results']) >= 1

    response = client.get(f'{different_schema_table_url}/{endpoint}/?{invalid_share_uuid_param}')
    response_data = response.json()
    assert response.status_code == different_schema_invalid_token_status
    if different_schema_invalid_token_status == 200:
        assert len(response_data['results']) >= 1
