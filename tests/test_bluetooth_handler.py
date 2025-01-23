import pytest
from bluetooth_handler import find_sensor, connect_to_sensor

@pytest.mark.asyncio
async def test_find_sensor_no_device_found(monkeypatch):
    async def mock_discover(*args, **kwargs):
        return []  # Simulate no devices found
    monkeypatch.setattr("bleak.BleakScanner.discover", mock_discover)

    address = await find_sensor()
    assert address is None, "Expected no devices to be found"

@pytest.mark.asyncio
async def test_connect_to_sensor_no_device(monkeypatch):
    async def mock_find_sensor():
        return None  # Simulate no sensor found
    monkeypatch.setattr("bluetooth_handler.find_sensor", mock_find_sensor)

    await connect_to_sensor()  # Should handle no sensor gracefully
