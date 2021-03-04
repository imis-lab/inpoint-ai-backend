from fastapi import FastAPI
#from server.routes.user import router as UserRouter
from server.routes.discourse_item import router as DiscourseItemRouter
from server.routes.discourse import router as DiscourseRouter

app = FastAPI(docs_url='/api/docs', redoc_url=None)

#app.include_router(UserRouter, tags=['Users'], prefix='/users')
app.include_router(DiscourseItemRouter, tags=['Discourse Items'], prefix='/api/discourse_items')
app.include_router(DiscourseRouter, tags=['Discourses'], prefix='/api/discourses')

@app.get('/', tags=['Root'])
async def read_root():
    return {'message': 'Welcome to this fantastic app!'}
