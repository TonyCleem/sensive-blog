from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count
from django.db.models import Prefetch


def get_related_posts_count(tag):
    return tag.posts.count()


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': len(Comment.objects.filter(post=post)),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }

def serialize_post_optimized(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag_optimized(tag) for tag in post.prefetch_tags],
        'first_tag_title': post.prefetch_tags[0].title,
    }

def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts.count()
    }

def serialize_tag_optimized(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.post_count
    }

def index(request):
    most_popular_posts = Post.objects.popular().select_related('author').prefetch_related(
        Prefetch(
            'tags',
            queryset=Tag.objects.annotate(post_count=Count('posts')),
            to_attr='prefetch_tags'))[:5] \
        .fetch_with_comments_count()

    most_fresh_posts = list(most_popular_posts)[-5:]

    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.select_related('author').prefetch_related('tags').get(slug=slug)
    comments = Comment.objects.select_related('author').filter(post=post)
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes = post.likes.all()

    related_tags = post.tags.all()

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': len(likes),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = Tag.objects.popular()[:5]

    most_popular_posts = Post.objects.popular().select_related('author').prefetch_related(
        Prefetch(
            'tags',
            queryset=Tag.objects.annotate(post_count=Count('posts')),
            to_attr='prefetch_tags'))[:5] \
        .fetch_with_comments_count()

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag_optimized(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.prefetch_related(
        Prefetch('posts', queryset=Post.objects.select_related('author').all(), to_attr='prefetch_posts'))\
        .get(title=tag_title)

    most_popular_posts = Post.objects.popular().select_related('author').prefetch_related(
        Prefetch(
            'tags',
            queryset=Tag.objects.annotate(post_count=Count('posts')),
            to_attr='prefetch_tags'))[:5] \
        .fetch_with_comments_count()

    related_posts = tag.prefetch_posts[:20]

    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag_optimized(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})


def get_likes_count(post):
    return post.count_likes