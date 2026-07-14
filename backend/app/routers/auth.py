from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.config.settings import settings
from backend.app.schemas import schemas
from backend.app.repositories.repositories import user_repo, tenant_repo, branch_repo
from backend.app.services import auth_service
from backend.app.models.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Logs in user and generates JWT access/refresh token pairs."""
    import logging
    logger = logging.getLogger("pharmacy_platform.auth")
    logger.info(f"Authenticating login request: username searched='{form_data.username}'")
    
    user = user_repo.get_by_username(db, form_data.username)
    if not user:
        logger.warning(f"Authentication failed: user '{form_data.username}' not found in database.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    logger.info(f"User '{form_data.username}' found in database. Stored hash: '{user.password_hash}'")
    is_valid = auth_service.verify_password(form_data.password, user.password_hash)
    logger.info(f"Bcrypt verification result for '{form_data.username}': {is_valid}")
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    token_data = {"sub": user.username, "role": user.role, "tenant_id": user.tenant_id, "branch_id": user.branch_id}
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=schemas.Token)
def refresh_token(token_payload: dict, db: Session = Depends(get_db)):
    """Refreshes access token using valid refresh token payload."""
    ref_token = token_payload.get("refresh_token")
    if not ref_token:
        raise HTTPException(status_code=400, detail="Missing refresh token")
        
    payload = auth_service.decode_token(ref_token, settings.JWT_REFRESH_SECRET)
    username = payload.get("sub")
    if not username or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    user = user_repo.get_by_username(db, username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
        
    new_token_data = {"sub": user.username, "role": user.role, "tenant_id": user.tenant_id, "branch_id": user.branch_id}
    new_access = auth_service.create_access_token(new_token_data)
    new_refresh = auth_service.create_refresh_token(new_token_data)
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer"
    }

@router.post("/signup", response_model=schemas.TenantResponse)
def signup_tenant(tenant_in: schemas.TenantCreate, db: Session = Depends(get_db)):
    """Registers a new healthcare group (tenant) alongside default admin user."""
    # 1. Create Tenant
    existing = tenant_repo.get_by_field(db, "company_name", tenant_in.company_name)
    if existing:
        raise HTTPException(status_code=400, detail="Healthcare group name already registered.")
        
    tenant = tenant_repo.create(db, {"company_name": tenant_in.company_name})
    
    # 2. Create Default Branch (Corporate HQ)
    branch = branch_repo.create(db, {
        "tenant_id": tenant.tenant_id,
        "branch_name": "Corporate HQ",
        "location": "All Locations"
    })
    
    # 3. Create Super-Admin User
    existing_user = user_repo.get_by_username(db, tenant_in.admin_username)
    if existing_user:
        # Rollback tenant
        tenant_repo.delete(db, tenant)
        raise HTTPException(status_code=400, detail="Username already registered.")
        
    user_repo.create(db, {
        "tenant_id": tenant.tenant_id,
        "branch_id": branch.branch_id,
        "username": tenant_in.admin_username,
        "password_hash": auth_service.hash_password(tenant_in.admin_password),
        "role": "Administrator",
        "full_name": tenant_in.admin_full_name
    })
    
    return tenant

@router.post("/branch", response_model=schemas.BranchResponse)
def create_branch(
    branch_in: schemas.BranchBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """Registers a new clinic branch location."""
    return branch_repo.create(db, {
        "tenant_id": current_user.tenant_id,
        "branch_name": branch_in.branch_name,
        "location": branch_in.location
    })

@router.post("/user", response_model=schemas.UserResponse)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.RoleChecker(["Administrator", "Branch Manager"]))
):
    """Registers a new user/operator staff account."""
    existing = user_repo.get_by_username(db, user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken.")
        
    return user_repo.create(db, {
        "tenant_id": current_user.tenant_id,
        "branch_id": user_in.branch_id if user_in.branch_id else current_user.branch_id,
        "username": user_in.username,
        "password_hash": auth_service.hash_password(user_in.password),
        "role": user_in.role,
        "full_name": user_in.full_name
    })

@router.get("/me")
def get_me(current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """Retrieves logged-in user profile, including group and branch names."""
    tenant_name = "Apex Rural Healthcare Group"
    if current_user.tenant:
        tenant_name = current_user.tenant.company_name
        
    branch_name = "All Branches"
    if current_user.branch:
        branch_name = current_user.branch.branch_name
        
    return {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "tenant_id": current_user.tenant_id,
        "branch_id": current_user.branch_id,
        "tenant_name": tenant_name,
        "branch_name": branch_name
    }

@router.get("/branches")
def list_branches(current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """Lists all branches under the user's tenant group."""
    return branch_repo.get_all_by_field(db, "tenant_id", current_user.tenant_id)
