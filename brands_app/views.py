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

from .forms import BrandModelForm
from .models import Brand
import os
import xml.etree.ElementTree as ET
from django.conf import settings
from .utils import validate_xml_tree, build_xml, save_xml_tree


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
                return redirect("/list/?source=db")  

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
                return redirect("/list/?source=xml")  

    else:
        form = BrandModelForm()

    return render(request, "brands_app/add_brand.html", {"form": form})

def upload_file(request):
    if request.method == "POST" and request.FILES.get("xml_file"):
        xml_file = request.FILES["xml_file"]

        try:
            # 1. Читаем и валидируем загруженный файл
            tree = etree.parse(xml_file)
            ok, msg = validate_xml_tree(tree)
            if not ok:
                messages.error(request, f"Файл невалиден: {msg}")
                return redirect("brands_app:upload_file")

            # 2. Собираем все записи из файла
            items = []
            for item in tree.getroot().findall("item"):
                name_el = item.find("name")
                country_el = item.find("country")
                if name_el is None or country_el is None:
                    continue

                name = (name_el.text or "").strip()
                country = (country_el.text or "").strip()

                # Проверка дубликата в БД
                if Brand.objects.filter(name__iexact=name, country__iexact=country).exists():
                    continue  # пропускаем, если уже есть в БД

                # Проверка дубликата в текущем загружаемом файле
                if any(
                    it.get("name", "").strip() == name and it.get("country", "").strip() == country
                    for it in items
                ):
                    continue

                # Добавляем запись
                data = {
                    "name": name,
                    "country": country,
                    "founded": (item.find("founded").text or "") if item.find("founded") is not None else "",
                    "note": (item.find("note").text or "") if item.find("note") is not None else "",
                    "color": (item.find("color").text or "") if item.find("color") is not None else "",
                }
                items.append(data)

            if not items:
                messages.info(request, "Нет новых записей для добавления (все дубликаты или пусто)")
                return redirect("brands_app:upload_file")

            # 3. Создаём НОВЫЙ файл с рандомным именем и сохраняем туда всё
            root = build_xml(items)
            filename = save_xml_tree(root)

            messages.success(request, f"Успешно добавлено {len(items)} записей → {filename}")
            return redirect("brands_app:list_items") + "?source=xml"

        except Exception as e:
            messages.error(request, f"Ошибка обработки файла: {e}")

    return render(request, "brands_app/upload_file.html")

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
