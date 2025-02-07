from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.oath2 import get_current_user
from .. import models, schemas, database, oath2
from typing import Optional
from sqlalchemy import func

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)


@router.get("/", response_model=List[schemas.PostOut])
def get_posts(db: Session = Depends(database.get_db), limit: int = 10, skip: int = 0, search: Optional[str] = ""):
    """
    Get all posts
    """
    # posts = db.query(models.Post).filter(models.Post.title.contains(search)).limit(limit).offset(skip).all()
    
    
    results = db.query(models.Post, func.count(models.Vote.post_id).label("votes")).join(
        models.Vote, models.Vote.post_id == models.Post.id, isouter=True).group_by(models.Post.id).filter(
            models.Post.title.contains(search)).limit(limit).offset(skip).all()
    print(results)
    return results



@router.get("/user/", response_model=List[schemas.Post])
def get_posts_by_user( db: Session = Depends(database.get_db), current_user: int = Depends(oath2.get_current_user)):
    """
    Get all posts by user

    """
    posts = db.query(models.Post).filter(models.Post.owner_id == current_user.id).all()
    return posts



@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Post)
def create_post(post: schemas.PostCreate, db: Session = Depends(database.get_db), current_user: int = Depends(oath2.get_current_user)):
    """
    Create a new post
    """
    new_post = models.Post(
        owner_id=current_user.id,
        owner=current_user,
        **post.dict()
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

@router.get("/{post_id}", response_model=schemas.PostOut)
def get_post(post_id: int, db: Session = Depends(database.get_db), current_user: int = Depends(oath2.get_current_user)):
    """
    Get a specific post by ID

    """
    
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    post_votes = db.query(models.Vote).filter(models.Vote.post_id == post_id).count()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
        
    return {"Post": post, "votes": post_votes}

@router.get("/latest/", response_model=schemas.Post)
def get_latest_post(db: Session = Depends(database.get_db)):
    """
    Get the latest post
    """
    post = db.query(models.Post).order_by(models.Post.created_at.desc()).first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No posts found"
        )
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(database.get_db), current_user: int = Depends(oath2.get_current_user)):
    """
    Delete a post
    """
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    post_query.delete(synchronize_session=False)
    db.commit()
    return None

@router.put("/{post_id}", response_model=schemas.Post)
def update_post(post_id: int, updated_post: schemas.PostUpdate, db: Session = Depends(database.get_db), current_user: int = Depends(oath2.get_current_user)):
    """
    Update a post
    """
    post_query = db.query(models.Post).filter(models.Post.id == post_id)
    post = post_query.first()
    
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    post_query.update(updated_post.dict(), synchronize_session=False)
    db.commit()
    return post_query.first()