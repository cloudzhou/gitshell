from django.db import models

class ToDoList(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    user_id = models.IntegerField(null=False, default=0) 
    scene_id = models.IntegerField(null=False, default=0)
    content = models.CharField(max_length=1024, default='')
    is_done = models.SmallIntegerField(default=0, null=False)

class Scene(models.Model):
    create_time = models.DateTimeField(auto_now=False, auto_now_add=True, null=False)
    modify_time = models.DateTimeField(auto_now=True, auto_now_add=True, null=False)
    visibly = models.SmallIntegerField(default=0, null=False)
    user_id = models.IntegerField(null=False, default=0) 
    name = models.CharField(max_length=32, default='')
    order = models.CharField(max_length=2048, default='')

class ToDoListManager():
    
    @classmethod
    def list_done_todo_by_userId_sceneId(self, user_id, scene_id, offset, row_count):
        todos = query(ToDoList, user_id, 'todolist_l_userId_sceneId_done', [user_id, scene_id, offset, row_count])
        return todos
    
    @classmethod
    def list_doing_todo_by_userId_sceneId(self, user_id, scene_id, offset, row_count):
        todos = query(ToDoList, user_id, 'todolist_l_userId_sceneId_doing', [user_id, scene_id, offset, row_count])
        return todos
    
    @classmethod
    def get_todo_by_id(self, user_id, todo_id):
        todos = query(ToDoList, user_id, 'todolist_l_userId_todoId', [user_id, todo_id])
        if len(todos) > 0:
            return todos[0]
        return None

    @classmethod
    def done_todo(self, user_id, todo_id):
        todo = self.get_todo_by_id(user_id, todo_id)
        if todo != None:
            todo.is_done = 1
            todo.save()

    @classmethod
    def doing_todo(self, user_id, todo_id):
        todo = self.get_todo_by_id(user_id, todo_id)
        if todo != None:
            todo.is_done = 0
            todo.save()

    @classmethod
    def remove_todo(self, user_id, todo_id):
        todo = self.get_todo_by_id(user_id, todo_id)
        if todo != None:
            todo.visibly = 1
            todo.save()

    @classmethod
    def list_scene_by_userId(self, user_id, offset, row_count):
        scenes = query(Scene, user_id, 'scene_l_userId', [user_id, offset, row_count])
        return scenes

    @classmethod
    def get_scene_by_id(self, user_id, scene_id):
        scenes = query(Scene, user_id, 'todolist_l_userId_sceneId', [user_id, scene_id])
        if len(scenes) > 0:
            return scenes[0]
        return None

    @classmethod
    def remove_scene(self, user_id, scene_id):
        scene = self.get_scene_by_id(user_id, scene_id)
        if scene != None:
            scene.save()


