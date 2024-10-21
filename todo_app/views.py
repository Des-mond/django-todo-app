from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Todo
from datetime import date

@login_required
def todo_list(request):
    filter_option = request.GET.get('filter', 'all')
    sort_option = request.GET.get('sort', 'created_at')

    todos = Todo.objects.filter(user=request.user)

    if filter_option == 'completed':
        todos = todos.filter(completed=True)
    elif filter_option == 'incomplete':
        todos = todos.filter(completed=False)

    if sort_option == 'due_date_asc':
        todos = todos.order_by('due_date')
    elif sort_option == 'due_date_desc':
        todos = todos.order_by('-due_date')
    elif sort_option == 'created_at_asc':
        todos = todos.order_by('created_at')
    elif sort_option == 'created_at_desc':
        todos = todos.order_by('-created_at')

    # Check for past due dates and set a message
    for todo in todos:
        if todo.due_date and todo.due_date < date.today() and not todo.completed:
            messages.warning(request, f"The task '{todo.title}' is past due. Please update the due date or mark it as completed.")

    context = {
        'todos': todos,
        'filter': filter_option,
        'sort': sort_option,
    }
    return render(request, 'todo_list.html', context)

@login_required
def todo_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        due_date = request.POST.get('due_date') or None
        if due_date and date.fromisoformat(due_date) < date.today():
            messages.error(request, "Due date cannot be in the past. Please select a future date.")
            return redirect('todo_list')
        Todo.objects.create(user=request.user, title=title, due_date=due_date)
        messages.success(request, "Task added successfully.")
        return redirect('todo_list')
    return redirect('todo_list')

@login_required
def todo_update(request, pk):
    todo = get_object_or_404(Todo, pk=pk, user=request.user)
    if request.method == 'POST':
        todo.title = request.POST.get('title')
        due_date = request.POST.get('due_date') or None
        if due_date and date.fromisoformat(due_date) < date.today():
            messages.error(request, "Due date cannot be in the past. Please select a future date.")
            return redirect('todo_list')
        todo.due_date = due_date
        todo.save()
        messages.success(request, "Task updated successfully.")
        return redirect('todo_list')
    
    # Only show the logged-in user's tasks
    context = {
        'todos': Todo.objects.filter(user=request.user).order_by('-created_at'),
        'edit_todo': todo,
    }
    return render(request, 'todo_list.html', context)

@login_required
def todo_delete(request, pk):
    if request.method == 'POST':
        todo = get_object_or_404(Todo, pk=pk, user=request.user)
        todo.delete()
        messages.success(request, "Task deleted successfully.")
    return redirect('todo_list')

@login_required
def todo_complete(request, pk):
    if request.method == 'POST':
        todo = get_object_or_404(Todo, pk=pk, user=request.user)
        todo.completed = not todo.completed
        todo.save()
        messages.success(request, f"Task marked as {'completed' if todo.completed else 'incomplete'}.")
    return redirect('todo_list')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('todo_list')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')