from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from models.schemas import Department, Employee, EmployeeCreate, EmployeeUpdate, OrgChart
from services.db import get_conn

router = APIRouter(prefix="/api/org", tags=["organization"])


@router.get("", response_model=OrgChart)
async def get_org_chart(username: str = Depends(verify_token)):
    """Get full organization chart with departments and employees."""
    conn = get_conn()
    dept_rows = conn.execute(
        "SELECT id, name, description, parent_id, sort_order FROM departments ORDER BY sort_order, id"
    ).fetchall()
    emp_rows = conn.execute(
        "SELECT id, name, department_id, position, role, email, phone, is_department_head FROM employees ORDER BY is_department_head DESC, id"
    ).fetchall()
    return OrgChart(
        departments=[
            Department(id=r[0], name=r[1], description=r[2], parent_id=r[3], sort_order=r[4])
            for r in dept_rows
        ],
        employees=[
            Employee(id=r[0], name=r[1], department_id=r[2], position=r[3], role=r[4], email=r[5], phone=r[6], is_department_head=r[7])
            for r in emp_rows
        ],
    )


@router.get("/departments", response_model=list[Department])
async def list_departments(username: str = Depends(verify_token)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, description, parent_id, sort_order FROM departments ORDER BY sort_order, id"
    ).fetchall()
    return [
        Department(id=r[0], name=r[1], description=r[2], parent_id=r[3], sort_order=r[4])
        for r in rows
    ]


@router.get("/departments/{dept_id}/employees", response_model=list[Employee])
async def get_department_employees(dept_id: int, username: str = Depends(verify_token)):
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, department_id, position, role, email, phone, is_department_head FROM employees WHERE department_id = ? ORDER BY is_department_head DESC, id",
        [dept_id],
    ).fetchall()
    return [
        Employee(id=r[0], name=r[1], department_id=r[2], position=r[3], role=r[4], email=r[5], phone=r[6], is_department_head=r[7])
        for r in rows
    ]


@router.get("/contact", response_model=list[Employee])
async def find_contact(q: str = "", username: str = Depends(verify_token)):
    """Find contact person by role keyword (e.g., '급여', '채용', '휴가')."""
    conn = get_conn()
    if not q:
        return []
    rows = conn.execute(
        """SELECT e.id, e.name, e.department_id, e.position, e.role, e.email, e.phone, e.is_department_head
           FROM employees e
           JOIN departments d ON e.department_id = d.id
           WHERE e.role ILIKE ? OR e.name ILIKE ? OR d.name ILIKE ?
           ORDER BY e.is_department_head DESC, e.id
           LIMIT 5""",
        [f"%{q}%", f"%{q}%", f"%{q}%"],
    ).fetchall()
    return [
        Employee(id=r[0], name=r[1], department_id=r[2], position=r[3], role=r[4], email=r[5], phone=r[6], is_department_head=r[7])
        for r in rows
    ]


@router.post("/employees", response_model=Employee)
async def create_employee(item: EmployeeCreate, username: str = Depends(verify_token)):
    conn = get_conn()
    result = conn.execute(
        "INSERT INTO employees (id, name, department_id, position, role, email, phone, is_department_head) VALUES (nextval('employees_id_seq'), ?, ?, ?, ?, ?, ?, ?) RETURNING id, name, department_id, position, role, email, phone, is_department_head",
        [item.name, item.department_id, item.position, item.role, item.email, item.phone, item.is_department_head],
    ).fetchone()
    return Employee(id=result[0], name=result[1], department_id=result[2], position=result[3], role=result[4], email=result[5], phone=result[6], is_department_head=result[7])


@router.put("/employees/{emp_id}", response_model=Employee)
async def update_employee(emp_id: int, item: EmployeeUpdate, username: str = Depends(verify_token)):
    conn = get_conn()
    existing = conn.execute("SELECT id FROM employees WHERE id = ?", [emp_id]).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Employee not found")

    updates = []
    params = []
    for field in ["name", "department_id", "position", "role", "email", "phone", "is_department_head"]:
        val = getattr(item, field)
        if val is not None:
            updates.append(f"{field} = ?")
            params.append(val)

    if updates:
        params.append(emp_id)
        conn.execute(f"UPDATE employees SET {', '.join(updates)} WHERE id = ?", params)

    row = conn.execute(
        "SELECT id, name, department_id, position, role, email, phone, is_department_head FROM employees WHERE id = ?", [emp_id]
    ).fetchone()
    return Employee(id=row[0], name=row[1], department_id=row[2], position=row[3], role=row[4], email=row[5], phone=row[6], is_department_head=row[7])


@router.delete("/employees/{emp_id}")
async def delete_employee(emp_id: int, username: str = Depends(verify_token)):
    conn = get_conn()
    conn.execute("DELETE FROM employees WHERE id = ?", [emp_id])
    return {"ok": True}
