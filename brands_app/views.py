from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .forms import BrandForm, BrandModelForm
from . import utils
from .config import MESSAGES
from .models import Brand
from lxml import etree
import os
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.db import models as dj_models
from django.http import JsonResponse
from django.contrib import messages
from .models import Brand
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import BrandModelForm
from .models import Brand
import os
import xml.etree.ElementTree as ET
from django.conf import settings


def add_brand(request):
    if request.method == "POST":
        form = BrandModelForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"].strip()
            country = form.cleaned_data["country"].strip()
            storage = form.cleaned_data["storage_choice"]

            # Проверка дубликата в БД
            if Brand.objects.filter(name__iexact=name, country__iexact=country).exists():
                messages.error(request, "Этот бренд уже есть в базе данных!")
                return render(request, "brands_app/add_brand.html", {"form": form})

            if storage == "db":
                form.save()
                messages.success(request, "Сохранено в базу данных!")
                return redirect("/list/?source=db")  # ← ИСПРАВЛЕНО

            else:
                # Сохранение в ОДИН файл all_brands.xml
                xml_path = os.path.join(settings.MEDIA_ROOT, "all_brands.xml")
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

                if not os.path.exists(xml_path):
                    root = etree.Element("brands")
                    tree = etree.ElementTree(root)
                    tree.write(xml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")

                tree = etree.parse(xml_path)
                root = tree.getroot()

                # Проверка дубликата в XML
                for item in root.findall("item"):
                    n = item.find("name")
                    c = item.find("country")
                    if n is not None and c is not None and n.text == name and c.text == country:
                        messages.error(request, "Этот бренд уже есть в XML!")
                        return render(request, "brands_app/add_brand.html", {"form": form})

                # Добавляем новый item
                new_item = etree.SubElement(root, "item")
                fields = ["name", "country", "founded", "note", "color"]
                for field in fields:
                    child = etree.SubElement(new_item, field)
                    value = form.cleaned_data[field]
                    child.text = str(value) if value not in ["", None] else ""

                tree.write(xml_path, pretty_print=True, xml_declaration=True, encoding="utf-8")
                messages.success(request, "Сохранено в XML!")
                return redirect("/list/?source=xml")  # ← ИСПРАВЛЕНО

    else:
        form = BrandModelForm()
        
    return render(request, "brands_app/add_brand.html", {"form": form})

def upload_file(request):
    # Оставляем без изменений (файловая загрузка XML)
    if request.method == "POST" and request.FILES.get("file"):
        f = request.FILES["file"]
        ext = os.path.splitext(f.name)[1].lower()
        if ext != ".xml":
            return render(request, "brands_app/upload_result.html", {"error": "Только .xml"})
        p = utils.storage_path()
        print(f"Storage path: {p}")
        os.makedirs(p, exist_ok=True)
        fname = f"{os.urandom(8).hex()}{ext}"
        full = os.path.join(p, fname)
        print(f"Saving file to: {full}")
        with open(full, "wb") as fh:
            for chunk in f.chunks():
                fh.write(chunk)
        # validate
        try:
            tree = etree.parse(full)
            ok, msg = utils.validate_xml_tree(tree)
            if not ok:
                os.remove(full)
                return render(request, "brands_app/upload_result.html", {"error": MESSAGES["upload_invalid"] + f" ({msg})"})
            print("File saved successfully")
            return render(request, "brands_app/upload_result.html", {"message": MESSAGES["upload_success"]})
        except Exception as e:
            print(f"Validation error: {str(e)}")
            if os.path.exists(full):
                os.remove(full)
            return render(request, "brands_app/upload_result.html", {"error": MESSAGES["upload_invalid"] + f" ({str(e)})"})
    return render(request, "brands_app/upload_result.html")

def list_items(request):
    # выбор источника: ?source=xml или ?source=db (по умолчанию xml)
    source = request.GET.get('source', 'xml')
    if source == 'db':
        brands = Brand.objects.all()
        return render(request, "brands_app/list.html", {"items": brands, "source": "db"})
    else:
        items = utils.read_all_xml()
        if not items:
            return render(request, "brands_app/uploaded_list.html", {"message": MESSAGES["no_files"], "items": []})
        return render(request, "brands_app/list.html", {"items": items, "source": "xml"})

# AJAX поиск по БД
def ajax_search(request):
    q = request.GET.get('q', '').strip()
    qs = Brand.objects.all()
    if q:
        qs = qs.filter(
            dj_models.Q(name__icontains=q) |
            dj_models.Q(country__icontains=q) |
            dj_models.Q(note__icontains=q) |
            dj_models.Q(color__icontains=q)
        )
    data = list(qs.values('id','name','country','founded','note','color'))
    return JsonResponse(data, safe=False)

# Редактирование записи в БД
def edit_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == "POST":
        form = BrandModelForm(request.POST, instance=brand)
        if form.is_valid():
            name = form.cleaned_data['name'].strip().lower()
            country = form.cleaned_data['country'].strip().lower()

            # Проверка: если это не текущий бренд — дубликат!
            if Brand.objects.filter(name__iexact=name, country__iexact=country).exclude(pk=pk).exists():
                return render(request, "brands_app/edit_brand.html", {
                    "form": form,
                    "brand": brand,
                    "error": "Бренд с таким именем и страной уже существует!"
                })

            form.save()
            return redirect('/list/?source=db')
    else:
        form = BrandModelForm(instance=brand)
    return render(request, "brands_app/edit_brand.html", {"form": form, "brand": brand})

# Удаление (AJAX POST)
@require_POST
def delete_brand(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    brand.delete()
    return JsonResponse({"status": "ok"})
