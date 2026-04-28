# file: modules/Tag_Hierarch/core/models.py
"""
Модели данных Tag Hierarch - Element, ItemList, ListManager.
"""

import json
import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Element:
    """Элемент иерархического списка."""
    name: str
    description: str = ""
    element_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    references: Dict[str, Dict[str, str]] = field(default_factory=dict)
    referenced_by: List[str] = field(default_factory=list)
    depends_on: Dict[str, str] = field(default_factory=dict)
    depended_by: Dict[str, str] = field(default_factory=dict)
    status: int = 0
    custom_status: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id, "name": self.name,
            "description": self.description, "parent_id": self.parent_id,
            "children_ids": self.children_ids, "references": self.references,
            "referenced_by": self.referenced_by,
            "depends_on": self.depends_on, "depended_by": self.depended_by,
            "status": self.status, "custom_status": self.custom_status,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Element":
        # Поддержка старых имен полей для обратной совместимости
        status_raw = data.get("status", data.get("state", 0))
        # Преобразуем строковые значения status в числа
        if isinstance(status_raw, str):
            status_map = {"active": 0, "blocked": -3, "pending": -1, "warning": 1}
            status = status_map.get(status_raw.lower(), 0)
        elif isinstance(status_raw, bool):
            # False -> 0, True -> 1 (но это редкость)
            status = 1 if status_raw else 0
        else:
            status = int(status_raw) if status_raw is not None else 0
            
        custom_status_raw = data.get("custom_status", data.get("custom_state"))
        # custom_status=False означает None (авто режим)
        if custom_status_raw is False:
            custom_status = None
        elif custom_status_raw is True:
            custom_status = 0
        elif isinstance(custom_status_raw, str):
            status_map = {"active": 0, "blocked": -3, "pending": -1, "warning": 1}
            custom_status = status_map.get(custom_status_raw.lower(), 0)
        else:
            custom_status = int(custom_status_raw) if custom_status_raw is not None else None
        
        # depends_on может быть списком (старый формат) или словарём {id: type} (новый формат)
        depends_on_raw = data.get("depends_on", {})
        if isinstance(depends_on_raw, list):
            # Старый формат: просто список ID, предполагаем тип "LE" по умолчанию
            depends_on = {dep_id: "LE" for dep_id in depends_on_raw}
        else:
            depends_on = depends_on_raw
            
        # depended_by может быть списком (старый формат) или словарём {id: type} (новый формат)
        depended_by_raw = data.get("depended_by", {})
        if isinstance(depended_by_raw, list):
            depended_by = {dep_id: "LE" for dep_id in depended_by_raw}
        else:
            depended_by = depended_by_raw
        
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            element_id=data["element_id"],
            parent_id=data.get("parent_id"),
            children_ids=data.get("children_ids", []),
            references=data.get("references", {}),
            referenced_by=data.get("referenced_by", []),
            depends_on=depends_on,
            depended_by=depended_by,
            status=status,
            custom_status=custom_status,
            metadata=data.get("metadata", {}),
        )


class ItemList:
    """Список элементов с иерархической структурой."""
    
    def __init__(self, list_id: str, name: str, description: str = ""):
        self.list_id = list_id
        self.name = name
        self.description = description
        self.elements: Dict[str, Element] = {}
        self.root_elements: List[str] = []

    def add_element(self, element: Element, parent_id: Optional[str] = None) -> Element:
        if parent_id and parent_id in self.elements:
            element.parent_id = parent_id
            self.elements[parent_id].children_ids.append(element.element_id)
        else:
            self.root_elements.append(element.element_id)
        self.elements[element.element_id] = element
        return element

    def remove_element(self, element_id: str, cascade: bool = False) -> List[str]:
        if element_id not in self.elements:
            return []
        removed = [element_id]
        element = self.elements[element_id]
        if element.parent_id and element.parent_id in self.elements:
            self.elements[element.parent_id].children_ids.remove(element_id)
        elif element_id in self.root_elements:
            self.root_elements.remove(element_id)
        if cascade:
            for child_id in element.children_ids[:]:
                removed.extend(self.remove_element(child_id, cascade=True))
        else:
            for child_id in element.children_ids:
                self.elements[child_id].parent_id = element.parent_id
                if element.parent_id:
                    self.elements[element.parent_id].children_ids.append(child_id)
                else:
                    self.root_elements.append(child_id)
        del self.elements[element_id]
        return removed

    def get_tree(self, element_id: Optional[str] = None, depth: int = 0) -> List[tuple]:
        result = []
        ids_to_process = [element_id] if element_id else self.root_elements
        for eid in ids_to_process:
            if eid in self.elements:
                elem = self.elements[eid]
                result.append((elem, depth))
                for child_id in elem.children_ids:
                    result.extend(self._get_subtree(child_id, depth + 1))
        return result

    def _get_subtree(self, element_id: str, depth: int) -> List[tuple]:
        result = []
        if element_id in self.elements:
            elem = self.elements[element_id]
            result.append((elem, depth))
            for child_id in elem.children_ids:
                result.extend(self._get_subtree(child_id, depth + 1))
        return result

    def to_dict(self) -> dict:
        return {
            "list_id": self.list_id, "name": self.name,
            "description": self.description,
            "elements": {eid: elem.to_dict() for eid, elem in self.elements.items()},
            "root_elements": self.root_elements,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ItemList":
        item_list = cls(data["list_id"], data["name"], data.get("description", ""))
        item_list.root_elements = data.get("root_elements", [])
        for eid, elem_data in data.get("elements", {}).items():
            item_list.elements[eid] = Element.from_dict(elem_data)
        return item_list


class ListManager:
    """Менеджер управления списками и элементами."""
    
    def __init__(self):
        self.lists: Dict[str, ItemList] = {}
        self._global_elements: Dict[str, str] = {}

    def create_list(self, name: str, description: str = "", list_id: Optional[str] = None) -> ItemList:
        lid = list_id or str(uuid.uuid4())
        item_list = ItemList(lid, name, description)
        self.lists[lid] = item_list
        return item_list

    def delete_list(self, list_id: str) -> bool:
        if list_id not in self.lists:
            return False
        for eid in list(self.lists[list_id].elements.keys()):
            self._remove_element_references(eid)
            if eid in self._global_elements:
                del self._global_elements[eid]
        del self.lists[list_id]
        return True

    def add_element(self, list_id: str, name: str, description: str = "",
                    parent_id: Optional[str] = None, element_id: Optional[str] = None) -> Optional[Element]:
        if list_id not in self.lists:
            return None
        element = Element(name=name, description=description, element_id=element_id or str(uuid.uuid4()))
        self.lists[list_id].add_element(element, parent_id)
        self._global_elements[element.element_id] = list_id
        return element

    def remove_element(self, list_id: str, element_id: str, cascade: bool = False) -> List[str]:
        if list_id not in self.lists:
            return []
        lst = self.lists[list_id]
        to_remove = [element_id]
        if cascade:
            self._collect_children(lst, element_id, to_remove)
        for eid in to_remove:
            self._remove_element_references(eid)
        removed = lst.remove_element(element_id, cascade)
        for eid in removed:
            if eid in self._global_elements:
                del self._global_elements[eid]
        return removed

    def _collect_children(self, lst: ItemList, element_id: str, result: List[str]):
        if element_id not in lst.elements:
            return
        for child_id in lst.elements[element_id].children_ids:
            result.append(child_id)
            self._collect_children(lst, child_id, result)

    def create_reference(self, from_element_id: str, to_element_id: str, note: str = ""):
        from_list_id = self._global_elements.get(from_element_id)
        to_list_id = self._global_elements.get(to_element_id)
        if not from_list_id or not to_list_id:
            raise ValueError("Один или оба элемента не найдены")
        from_elem = self.lists[from_list_id].elements[from_element_id]
        from_elem.references[to_element_id] = {"list_id": to_list_id, "note": note}
        to_elem = self.lists[to_list_id].elements[to_element_id]
        if from_element_id not in to_elem.referenced_by:
            to_elem.referenced_by.append(from_element_id)
        to_elem.references[from_element_id] = {"list_id": from_list_id, "note": note}
        if to_element_id not in from_elem.referenced_by:
            from_elem.referenced_by.append(to_element_id)

    def remove_reference(self, from_element_id: str, to_element_id: str):
        from_list_id = self._global_elements.get(from_element_id)
        to_list_id = self._global_elements.get(to_element_id)
        if from_list_id and from_element_id in self.lists[from_list_id].elements:
            elem = self.lists[from_list_id].elements[from_element_id]
            if to_element_id in elem.references:
                del elem.references[to_element_id]
        if to_list_id and to_element_id in self.lists[to_list_id].elements:
            elem = self.lists[to_list_id].elements[to_element_id]
            if from_element_id in elem.referenced_by:
                elem.referenced_by.remove(from_element_id)
        if to_list_id and to_element_id in self.lists[to_list_id].elements:
            elem = self.lists[to_list_id].elements[to_element_id]
            if from_element_id in elem.references:
                del elem.references[from_element_id]
        if from_list_id and from_element_id in self.lists[from_list_id].elements:
            elem = self.lists[from_list_id].elements[from_element_id]
            if to_element_id in elem.referenced_by:
                elem.referenced_by.remove(to_element_id)

    def add_dependency(self, element_id: str, depends_on_id: str, dep_type: str = "LE"):
        list_id = self._global_elements.get(element_id)
        dep_list_id = self._global_elements.get(depends_on_id)
        if list_id and element_id in self.lists[list_id].elements:
            self.lists[list_id].elements[element_id].depends_on[depends_on_id] = dep_type
        if dep_list_id and depends_on_id in self.lists[dep_list_id].elements:
            self.lists[dep_list_id].elements[depends_on_id].depended_by[element_id] = dep_type

    def remove_dependency(self, element_id: str, depends_on_id: str):
        list_id = self._global_elements.get(element_id)
        dep_list_id = self._global_elements.get(depends_on_id)
        if list_id and element_id in self.lists[list_id].elements:
            elem = self.lists[list_id].elements[element_id]
            if depends_on_id in elem.depends_on:
                del elem.depends_on[depends_on_id]
        if dep_list_id and depends_on_id in self.lists[dep_list_id].elements:
            dep_elem = self.lists[dep_list_id].elements[depends_on_id]
            if element_id in dep_elem.depended_by:
                del dep_elem.depended_by[element_id]

    def set_element_custom_status(self, element_id: str, status: Optional[int] = None):
        list_id = self._global_elements.get(element_id)
        if not list_id:
            return
        self.lists[list_id].elements[element_id].custom_status = status
        self._recalculate_states()

    def _recalculate_states(self):
        visited, temp_mark, order = set(), set(), []

        def visit(eid):
            if eid in temp_mark:
                return
            if eid in visited:
                return
            temp_mark.add(eid)
            lid = self._global_elements.get(eid)
            if lid and eid in self.lists[lid].elements:
                for dep_id in self.lists[lid].elements[eid].depends_on.keys():
                    visit(dep_id)
            temp_mark.remove(eid)
            visited.add(eid)
            order.append(eid)

        all_elements = [eid for lst in self.lists.values() for eid in lst.elements.keys()]
        for eid in all_elements:
            if eid not in visited:
                visit(eid)

        for eid in order:
            lid = self._global_elements.get(eid)
            if not lid:
                continue
            elem = self.lists[lid].elements[eid]
            if elem.custom_status is not None:
                elem.status = max(-3, min(3, elem.custom_status))
                continue

            low, high = -3, 3
            if elem.parent_id:
                parent_lid = self._global_elements.get(elem.parent_id)
                if parent_lid and elem.parent_id in self.lists[parent_lid].elements:
                    high = min(high, self.lists[parent_lid].elements[elem.parent_id].status)

            for dep_id, dep_type in elem.depends_on.items():
                dep_lid = self._global_elements.get(dep_id)
                if not dep_lid or dep_id not in self.lists[dep_lid].elements:
                    continue
                s = self.lists[dep_lid].elements[dep_id].status
                if dep_type == "EQ":
                    low = max(low, s)
                    high = min(high, s)
                elif dep_type == "PM1":
                    low = max(low, s - 1)
                    high = min(high, s + 1)
                elif dep_type == "LE":
                    high = min(high, s)
                elif dep_type == "GE":
                    low = max(low, s)

            if low > high:
                elem.status = -3
            else:
                if low <= 0 <= high:
                    elem.status = 0
                elif high < 0:
                    elem.status = high
                else:
                    elem.status = low

    def get_element_info(self, element_id: str) -> Optional[dict]:
        lid = self._global_elements.get(element_id)
        if not lid or element_id not in self.lists[lid].elements:
            return None
        elem = self.lists[lid].elements[element_id]
        info = elem.to_dict()
        info["list_id"] = lid
        info["list_name"] = self.lists[lid].name

        info["resolved_references"] = []
        for ref_id, ref_data in elem.references.items():
            ref_lid = self._global_elements.get(ref_id)
            if ref_lid and ref_id in self.lists[ref_lid].elements:
                ref_elem = self.lists[ref_lid].elements[ref_id]
                info["resolved_references"].append({
                    "element_id": ref_id, "name": ref_elem.name,
                    "list_name": self.lists[ref_lid].name,
                    "note": ref_data.get("note", ""),
                })

        info["resolved_dependencies"] = []
        for dep_id, dep_type in elem.depends_on.items():
            dep_lid = self._global_elements.get(dep_id)
            if dep_lid and dep_id in self.lists[dep_lid].elements:
                dep_elem = self.lists[dep_lid].elements[dep_id]
                info["resolved_dependencies"].append({
                    "element_id": dep_id, "name": dep_elem.name,
                    "status": dep_elem.status, "type": dep_type,
                })

        info["resolved_depended_by"] = []
        for dep_by_id, dep_type in elem.depended_by.items():
            dep_by_lid = self._global_elements.get(dep_by_id)
            if dep_by_lid and dep_by_id in self.lists[dep_by_lid].elements:
                dep_by_elem = self.lists[dep_by_lid].elements[dep_by_id]
                info["resolved_depended_by"].append({
                    "element_id": dep_by_id, "name": dep_by_elem.name,
                    "status": dep_by_elem.status, "type": dep_type,
                    "list_name": self.lists[dep_by_lid].name,
                })

        info["children"] = []
        for child_id in elem.children_ids:
            if child_id in self.lists[lid].elements:
                child = self.lists[lid].elements[child_id]
                info["children"].append({
                    "element_id": child_id, "name": child.name,
                    "status": child.status,
                })
        return info

    def export_to_json(self, filepath: Optional[str] = None) -> Optional[str]:
        data = {
            "lists": {lid: lst.to_dict() for lid, lst in self.lists.items()},
            "global_elements": self._global_elements,
        }
        if filepath is None:
            return json.dumps(data, ensure_ascii=False, indent=2)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return None

    def import_from_json(self, filepath: Optional[str] = None, json_str: Optional[str] = None):
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif json_str:
            data = json.loads(json_str)
        else:
            raise ValueError("Необходимо указать либо filepath, либо json_str")
        self.lists = {}
        self._global_elements = data.get("global_elements", {})
        for lid, lst_data in data.get("lists", {}).items():
            self.lists[lid] = ItemList.from_dict(lst_data)
        # Пересчитать статусы после загрузки
        self._recalculate_states()

    def _remove_element_references(self, element_id: str):
        lid = self._global_elements.get(element_id)
        if not lid or element_id not in self.lists[lid].elements:
            return
        elem = self.lists[lid].elements[element_id]
        for ref_id in list(elem.references.keys()):
            self.remove_reference(element_id, ref_id)
        for ref_by_id in elem.referenced_by[:]:
            self.remove_reference(ref_by_id, element_id)
        for dep_id in list(elem.depends_on.keys()):
            self.remove_dependency(element_id, dep_id)
        for dep_by_id in list(elem.depended_by.keys()):
            self.remove_dependency(dep_by_id, element_id)

    def get_all_elements_flat(self) -> List[dict]:
        result = []
        for lst in self.lists.values():
            for elem in lst.elements.values():
                result.append({
                    "element_id": elem.element_id, "name": elem.name,
                    "list_id": lst.list_id, "list_name": lst.name,
                })
        return result
