from typing import List
from uuid import UUID
from langflow.api.schemas import FlowListCreate
from langflow.database.models.flow import Flow, FlowCreate, FlowRead
from langflow.database.base import get_session
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException


from fastapi import File, UploadFile
import json

# build router
router = APIRouter(prefix="/flows", tags=["Flows"])


@router.post("/", response_model=FlowRead)
def create_flow(*, session: Session = Depends(get_session), flow: FlowCreate):
    """Create a new flow."""
    db_flow = Flow.from_orm(flow)
    session.add(db_flow)
    session.commit()
    session.refresh(db_flow)
    return db_flow


@router.get("/", response_model=list[FlowRead])
def read_flows(*, session: Session = Depends(get_session)):
    """Read all flows."""
    flows = session.exec(select(Flow)).all()
    return flows


@router.get("/{flow_id}", response_model=FlowRead)
def read_flow(*, session: Session = Depends(get_session), flow_id: UUID):
    """Read a flow."""
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return flow


@router.put("/{flow_id}", response_model=FlowRead)
def update_flow(
    *, session: Session = Depends(get_session), flow_id: UUID, flow: FlowCreate
):
    """Update a flow."""
    db_flow = session.get(Flow, flow_id)
    if not db_flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    update_data = flow.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_flow, key, value)
    session.add(db_flow)
    session.commit()
    session.refresh(db_flow)
    return db_flow


@router.delete("/{flow_id}")
def delete_flow(*, session: Session = Depends(get_session), flow_id: UUID):
    """Delete a flow."""
    flow = session.get(Flow, flow_id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    session.delete(flow)
    session.commit()
    return {"message": "Flow deleted successfully"}


# Define a new model to handle multiple flows


@router.post("/batch/", response_model=List[FlowRead])
def create_flows(*, session: Session = Depends(get_session), flow_list: FlowListCreate):
    """Create multiple new flows."""
    db_flows = []
    for flow in flow_list.flows:
        db_flow = Flow.from_orm(flow)
        session.add(db_flow)
        db_flows.append(db_flow)
    session.commit()
    for db_flow in db_flows:
        session.refresh(db_flow)
    return db_flows


@router.post("/upload/", response_model=List[FlowRead])
async def upload_file(
    *, session: Session = Depends(get_session), file: UploadFile = File(...)
):
    """Upload flows from a file."""
    contents = await file.read()
    data = json.loads(contents)
    if "flows" in data:
        flow_list = FlowListCreate(**data)
    else:
        flow_list = FlowListCreate(flows=[FlowCreate(**flow) for flow in data])
    return create_flows(session=session, flow_list=flow_list)


@router.get("/download/")
async def download_file(*, session: Session = Depends(get_session)):
    """Download all flows as a file."""
    flows = read_flows(session=session)
    return {"file": json.dumps([flow.dict() for flow in flows], default=str)}