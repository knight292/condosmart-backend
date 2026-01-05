from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db import get_db
from app.models import InventoryItem, User
from app.schemas.inventory import InventoryItemCreate, InventoryItemUpdate, InventoryItemResponse
from app.auth import get_current_user

router = APIRouter()

@router.post("/", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    item_data: InventoryItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create inventory items"
        )
    
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    new_item = InventoryItem(
        condominium_id=current_user.condominium_id,
        created_by=current_user.id,
        name=item_data.name,
        description=item_data.description,
        category=item_data.category,
        location=item_data.location,
        quantity=item_data.quantity,
        condition=item_data.condition,
        purchase_date=item_data.purchase_date,
        purchase_price=item_data.purchase_price,
        serial_number=item_data.serial_number,
        brand=item_data.brand,
        model=item_data.model,
        notes=item_data.notes
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    item_dict = {
        "id": new_item.id,
        "condominium_id": new_item.condominium_id,
        "created_by": new_item.created_by,
        "name": new_item.name,
        "description": new_item.description,
        "category": new_item.category,
        "location": new_item.location,
        "quantity": new_item.quantity,
        "condition": new_item.condition,
        "purchase_date": new_item.purchase_date,
        "purchase_price": new_item.purchase_price,
        "serial_number": new_item.serial_number,
        "brand": new_item.brand,
        "model": new_item.model,
        "is_active": new_item.is_active,
        "notes": new_item.notes,
        "created_at": new_item.created_at,
        "updated_at": new_item.updated_at,
        "creator_name": current_user.full_name,
    }
    return item_dict

@router.get("/", response_model=List[InventoryItemResponse])
def get_inventory_items(
    category: Optional[str] = None,
    location: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.condominium_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to a condominium"
        )
    
    query = db.query(InventoryItem).filter(
        InventoryItem.condominium_id == current_user.condominium_id,
        InventoryItem.is_active == True
    )
    
    if category:
        query = query.filter(InventoryItem.category == category)
    
    if location:
        query = query.filter(InventoryItem.location == location)
    
    items = query.order_by(InventoryItem.name.asc()).all()
    
    result = []
    for item in items:
        creator = db.query(User).filter(User.id == item.created_by).first()
        item_dict = {
            "id": item.id,
            "condominium_id": item.condominium_id,
            "created_by": item.created_by,
            "name": item.name,
            "description": item.description,
            "category": item.category,
            "location": item.location,
            "quantity": item.quantity,
            "condition": item.condition,
            "purchase_date": item.purchase_date,
            "purchase_price": item.purchase_price,
            "serial_number": item.serial_number,
            "brand": item.brand,
            "model": item.model,
            "is_active": item.is_active,
            "notes": item.notes,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "creator_name": creator.full_name if creator else None,
        }
        result.append(item_dict)
    
    return result

@router.patch("/{item_id}", response_model=InventoryItemResponse)
def update_inventory_item(
    item_id: str,
    item_data: InventoryItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update inventory items"
        )
    
    item = db.query(InventoryItem).filter(InventoryItem.id == UUID(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    if item.condominium_id != current_user.condominium_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = item_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    
    creator = db.query(User).filter(User.id == item.created_by).first()
    item_dict = {
        "id": item.id,
        "condominium_id": item.condominium_id,
        "created_by": item.created_by,
        "name": item.name,
        "description": item.description,
        "category": item.category,
        "location": item.location,
        "quantity": item.quantity,
        "condition": item.condition,
        "purchase_date": item.purchase_date,
        "purchase_price": item.purchase_price,
        "serial_number": item.serial_number,
        "brand": item.brand,
        "model": item.model,
        "is_active": item.is_active,
        "notes": item.notes,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "creator_name": creator.full_name if creator else None,
    }
    return item_dict

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete inventory items"
        )
    
    item = db.query(InventoryItem).filter(InventoryItem.id == UUID(item_id)).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    
    if item.condominium_id != current_user.condominium_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Soft delete
    item.is_active = False
    db.commit()
    return None

