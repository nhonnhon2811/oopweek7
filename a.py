#****************

#202419001  

#Đặng Nhật Trọng

#****************
from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeVar, Generic, List, Optional, Callable, Set, Any

# ==========================================
# 1. Khai báo Ngoại lệ (Exceptions)
# ==========================================
class DuplicateIdException(Exception):
    def __init__(self, duplicate_id: str):
        self.duplicate_id = duplicate_id
        super().__init__(f"Phần tử với Id '{duplicate_id}' đã tồn tại.")

class NoSuitableItemException(Exception):
    def __init__(self, message: str = "Không tìm thấy thiết bị phù hợp."):
        super().__init__(message)

class DeviceNotReadyException(Exception):
    def __init__(self, device_id: str, current_status: 'DeviceStatus'):
        self.device_id = device_id
        self.current_status = current_status
        super().__init__(f"Thiết bị '{device_id}' không sẵn sàng (Trạng thái hiện tại: {current_status.value}).")


# ==========================================
# 1. Quy tắc nghiệp vụ & Trạng thái
# ==========================================
class DeviceStatus(Enum):
    Available = "Available"
    Borrowed = "Borrowed"
    UnderMaintenance = "UnderMaintenance"


# ==========================================
# 3. Thiết kế lớp thiết bị và đa hình
# ==========================================
class IIdentifiable(ABC):
    @property
    @abstractmethod
    def id(self) -> str:
        pass


class TeachingDevice(IIdentifiable):
    def __init__(self, device_id: str, name: str, storage_location: str):
        if not device_id or not name or not storage_location:
            raise ValueError("Id, Name và StorageLocation không được để trống.")
        self._id = device_id
        self._name = name
        self._storage_location = storage_location
        self._status = DeviceStatus.Available

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def storage_location(self) -> str:
        return self._storage_location

    @property
    def status(self) -> DeviceStatus:
        return self._status

    @abstractmethod
    def is_ready_for_use(self) -> bool:
        pass

    @abstractmethod
    def get_default_priority_score(self) -> float:
        pass

    def borrow(self) -> bool:
        if self.is_ready_for_use():
            self._status = DeviceStatus.Borrowed
            return True
        return False

    def return_device(self) -> bool:
        if self._status == DeviceStatus.Borrowed:
            self._status = DeviceStatus.Available
            return True
        return False


class ProjectorRemote(TeachingDevice):
    def __init__(self, device_id: str, name: str, storage_location: str, battery_level: int):
        super().__init__(device_id, name, storage_location)
        self._battery_level = battery_level

    @property
    def battery_level(self) -> int:
        return self._battery_level

    def is_ready_for_use(self) -> bool:
        return self.status == DeviceStatus.Available and self._battery_level >= 20

    def get_default_priority_score(self) -> float:
        return float(self._battery_level)


class AirConditionerRemote(TeachingDevice):
    def __init__(self, device_id: str, name: str, storage_location: str, compatible_rooms: Set[str]):
        super().__init__(device_id, name, storage_location)
        self._compatible_rooms: Set[str] = set(compatible_rooms)

    @property
    def compatible_rooms(self) -> Set[str]:
        return self._compatible_rooms

    def is_compatible_with(self, room_id: str) -> bool:
        return room_id in self._compatible_rooms

    def is_ready_for_use(self) -> bool:
        return self.status == DeviceStatus.Available

    def get_default_priority_score(self) -> float:
        return 100.0


class WirelessMicrophone(TeachingDevice):
    def __init__(self, device_id: str, name: str, storage_location: str, battery_level: int, signal_quality: int):
        super().__init__(device_id, name, storage_location)
        self._battery_level = battery_level
        self._signal_quality = signal_quality

    @property
    def battery_level(self) -> int:
        return self._battery_level

    @property
    def signal_quality(self) -> int:
        return self._signal_quality

    def is_ready_for_use(self) -> bool:
        return (
            self.status == DeviceStatus.Available
            and self._battery_level >= 30
            and self._signal_quality >= 40
        )

    def get_default_priority_score(self) -> float:
        return (self._battery_level + self._signal_quality) / 2.0


# ==========================================
# 4. Kho lưu trữ tổng quát (Generic Repository)
# ==========================================
T = TypeVar('T', bound=IIdentifiable)
TD = TypeVar('TD', bound=TeachingDevice)

class IRepository(Generic[T], ABC):
    @abstractmethod
    def add(self, item: T) -> None:
        pass

    @abstractmethod
    def remove(self, item_id: str) -> bool:
        pass

    @abstractmethod
    def find_by_id(self, item_id: str) -> Optional[T]:
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        pass

    @abstractmethod
    def find_all(self, condition: Callable[[T], bool]) -> List[T]:
        pass


class InMemoryRepository(IRepository[T]):
    def __init__(self):
        self._items: dict[str, T] = {}

    def add(self, item: T) -> None:
        if item is None:
            raise ValueError("Phần tử không được là None.")
        if item.id in self._items:
            raise DuplicateIdException(item.id)
        self._items[item.id] = item

    def remove(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def find_by_id(self, item_id: str) -> Optional[T]:
        return self._items.get(item_id, None)

    def get_all(self) -> List[T]:
        # Trả về bản sao danh sách để không làm lộ collection nội bộ
        return list(self._items.values())

    def find_all(self, condition: Callable[[T], bool]) -> List[T]:
        return [item for item in self._items.values() if condition(item)]


# ==========================================
# 5. Chiến lược lựa chọn thiết bị bằng đa hình và generic
# ==========================================
class ISelectionStrategy(Generic[T], ABC):
    @abstractmethod
    def select(self, candidates: List[T]) -> T:
        pass


class HighestPriorityStrategy(ISelectionStrategy[T]):
    def __init__(self, score_selector: Callable[[T], float]):
        self._score_selector = score_selector

    def select(self, candidates: List[T]) -> T:
        if not candidates:
            raise NoSuitableItemException("Danh sách ứng viên rỗng.")
        return max(candidates, key=self._score_selector)


class FirstAvailableStrategy(ISelectionStrategy[T]):
    def select(self, candidates: List[T]) -> T:
        if not candidates:
            raise NoSuitableItemException("Danh sách ứng viên rỗng.")
        return candidates[0]


# ==========================================
# 6. Dịch vụ cấp phát tổng quát
# ==========================================
class AllocationService(Generic[TD]):
    def __init__(self, repository: IRepository[TD], strategy: ISelectionStrategy[TD]):
        self._repository = repository
        self._strategy = strategy

    def change_strategy(self, new_strategy: ISelectionStrategy[TD]) -> None:
        self._strategy = new_strategy

    def allocate(self, additional_condition: Optional[Callable[[TD], bool]] = None) -> TD:
        # 1 & 2. Lấy thiết bị và chỉ giữ những thiết bị IsReadyForUse() == True
        candidates = self._repository.find_all(lambda d: d.is_ready_for_use())
        
        # 3. Áp dụng additionalCondition nếu được cung cấp
        if additional_condition:
            candidates = [d for d in candidates if additional_condition(d)]
            
        # 4. Dùng chiến lược hiện tại để chọn thiết bị
        selected_device = self._strategy.select(candidates)
        
        # 5. Gọi Borrow() trên thiết bị được chọn
        selected_device.borrow()
        
        # 6. Trả về thiết bị đã cấp phát
        return selected_device


# ==========================================
# 9. Kiểm thử (Test Script)
# ==========================================
if __name__ == "__main__":
    print("=== BẮT ĐẦU KIỂM THỬ HỆ THỐNG QUẢN LÝ THIẾT BỊ ===\n")

    # Tạo Repository
    projector_repo = InMemoryRepository[ProjectorRemote]()
    ac_repo = InMemoryRepository[AirConditionerRemote]()
    mic_repo = InMemoryRepository[WirelessMicrophone]()

    # 1. Thêm thiết bị vào repository
    # 3 Điều khiển máy chiếu (Pin khác nhau)
    p1 = ProjectorRemote("PR01", "Máy chiếu 1", "Kho A", battery_level=15) # Không sẵn sàng (pin < 20)
    p2 = ProjectorRemote("PR02", "Máy chiếu 2", "Kho A", battery_level=50)
    p3 = ProjectorRemote("PR03", "Máy chiếu 3", "Kho B", battery_level=90)
    for p in [p1, p2, p3]:
        projector_repo.add(p)

    # 2 Điều khiển điều hòa (Phòng tương thích khác nhau)
    ac1 = AirConditionerRemote("AC01", "Điều hòa A", "Kho A", {"A201", "A202"})
    ac2 = AirConditionerRemote("AC02", "Điều hòa B", "Kho B", {"A203", "A204"})
    ac_repo.add(ac1)
    ac_repo.add(ac2)

    # 3 Micro (Pin và Tín hiệu khác nhau)
    m1 = WirelessMicrophone("MIC01", "Micro 1", "Kho C", battery_level=80, signal_quality=30) # Tín hiệu kém
    m2 = WirelessMicrophone("MIC02", "Micro 2", "Kho C", battery_level=70, signal_quality=80) # Điểm TB: 75
    m3 = WirelessMicrophone("MIC03", "Micro 3", "Kho C", battery_level=90, signal_quality=90) # Điểm TB: 90
    for m in [m1, m2, m3]:
        mic_repo.add(m)

    print("1. Thêm thành công các thiết bị mẫu.")

    # 2. Thử thêm hai thiết bị trùng mã
    print("\n2. Kiểm thử thêm thiết bị trùng mã:")
    try:
        projector_repo.add(ProjectorRemote("PR01", "Trùng mã", "Kho A", 100))
    except DuplicateIdException as e:
        print(f"   [Thành công bắt lỗi]: {e}")

    # 3. Tìm thiết bị theo mã
    print("\n3. Kiểm thử tìm thiết bị theo mã:")
    found_p = projector_repo.find_by_id("PR02")
    print(f"   Tìm PR02: {found_p.name if found_p else 'Không thấy'}")

    # 4. Lọc các thiết bị sẵn sàng
    print("\n4. Lọc các thiết bị Máy chiếu sẵn sàng cấp phát:")
    ready_projectors = projector_repo.find_all(lambda d: d.is_ready_for_use())
    for r in ready_projectors:
        print(f"   - {r.id}: {r.name} (Pin: {r.battery_level}%)")

    # 5. Chọn điều khiển máy chiếu có điểm ưu tiên cao nhất
    print("\n5. Chọn máy chiếu điểm cao nhất:")
    proj_strategy = HighestPriorityStrategy[ProjectorRemote](lambda d: d.get_default_priority_score())
    proj_service = AllocationService[ProjectorRemote](projector_repo, proj_strategy)
    allocated_proj = proj_service.allocate()
    print(f"   Đã cấp phát: {allocated_proj.id} - Pin: {allocated_proj.battery_level}%")

    # 6. Chọn điều khiển điều hòa tương thích với phòng A203
    print("\n6. Chọn điều hòa tương thích phòng A203:")
    ac_strategy = FirstAvailableStrategy[AirConditionerRemote]()
    ac_service = AllocationService[AirConditionerRemote](ac_repo, ac_strategy)
    allocated_ac = ac_service.allocate(additional_condition=lambda d: d.is_compatible_with("A203"))
    print(f"   Đã cấp phát: {allocated_ac.id} cho phòng A203")

    # 7. Chọn micro đầu tiên sẵn sàng
    print("\n7. Chọn micro đầu tiên sẵn sàng:")
    mic_strategy = FirstAvailableStrategy[WirelessMicrophone]()
    mic_service = AllocationService[WirelessMicrophone](mic_repo, mic_strategy)
    allocated_mic = mic_service.allocate()
    print(f"   Đã cấp phát: {allocated_mic.id}")

    # 8. Đổi chiến lược trong thời gian chạy (Runtime) và quan sát kết quả
    print("\n8. Đổi chiến lược micro sang HighestPriorityStrategy:")
    high_priority_mic_strategy = HighestPriorityStrategy[WirelessMicrophone](lambda m: m.get_default_priority_score())
    mic_service.change_strategy(high_priority_mic_strategy)
    allocated_mic_2 = mic_service.allocate()
    print(f"   Đã cấp phát micro điểm cao nhất: {allocated_mic_2.id} (Điểm: {allocated_mic_2.get_default_priority_score()})")

    # 9. Thử cấp phát khi không có ứng viên phù hợp
    print("\n9. Kiểm thử cấp phát khi không có ứng viên phù hợp (Tìm điều hòa phòng XYZ):")
    try:
        ac_service.allocate(additional_condition=lambda d: d.is_compatible_with("XYZ"))
    except NoSuitableItemException as e:
        print(f"   [Thành công bắt lỗi]: {e}")

    # 10. Chứng minh thiết bị được chọn chuyển sang Borrowed
    print("\n10. Kiểm tra trạng thái thiết bị đã cấp phát:")
    print(f"   Trạng thái PR03 sau khi mượn: {allocated_proj.status.value}")

    # 11. Chứng minh repository tổng quát có thể dùng cho nhiều loại thiết bị mà không sao chép mã
    print("\n11. Kiểm tra tính tái sử dụng của Generic Repository:")
    print(f"   ProjectorRepo class: {type(projector_repo).__name__}")
    print(f"   ACRepo class:        {type(ac_repo).__name__}")
    print(f"   MicRepo class:       {type(mic_repo).__name__}")
    
    print("\n=== TẤT CẢ BÀI KIỂM THỬ ĐÃ HOÀN THÀNH TỐT ===")