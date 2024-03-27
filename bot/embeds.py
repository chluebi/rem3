from discord import Embed, Color

blue = Color.blue()
red = Color.red()
green = Color.green()
teal = Color.teal()
gray = Color.lighter_gray()

def standard_embed(title, description, color=blue, ctx=None):
    embed = Embed(title=title, description=description, color=color)
    if ctx is not None:
        embed.set_footer(text=f'Command Invoked by {str(ctx.author)}', icon_url=ctx.author.display_avatar.url)
    return embed

def success_embed(title, description, ctx):
    return standard_embed(title, description, color=green, ctx=ctx)

def info_embed(title, description, ctx):
    return standard_embed('Info', description, color=gray)

def error_embed(title, description, ctx):
    return standard_embed(title, description, color=red)


def list_embed(title, description, list, color=blue, ctx=None):
    
    pages = [['']]

    for item in list:
        if sum(map(len, pages[-1]))*1.1 + len(item) > 5500:
            pages.append([item])
        elif len(pages[-1][-1])*1.1 + len(item) > 1024:
            pages[-1].append(item)
        else:
            pages[-1][-1] += '\n' + item

    if len(pages) > 10:
        raise ValueError('Too many pages')

    embeds = []

    for i, page in enumerate(pages, 1):
        embed = standard_embed(title, description, color=color)
        if ctx is None:
            embed.set_footer(text=f'Page {i}/{len(pages)}')
        else:
            embed.set_footer(text=f'Page {i}/{len(pages)} Command Invoked by {str(ctx.author)}', icon_url=ctx.author.display_avatar.url)
        for j, field in enumerate(page, 1):
            embed.add_field(name=f'Page {i}: {j}/{len(page)}', value=field)
        embeds.append(embed)
    
    return embeds
