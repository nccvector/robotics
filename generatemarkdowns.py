import os
import argparse
import glob
import subprocess


parser = argparse.ArgumentParser(description='Process deploy flags')
parser.add_argument('--deploy', action='store_true', help='Removes notebooks')

# Parsing arguments
args = parser.parse_args()


# Find all jupyter notebooks
rootDir = os.getcwd()
print('Python execution root directory: ', rootDir)


def ConsoleLog(message):
    subprocess.run(['echo', message])


def GetFileCreationDate(filepath):
    out = subprocess.check_output([
        'git', 'log', '--follow', '--format=%ad', '--date=iso', filepath
    ]).decode('utf-8')

    return out.split('\n')[-2]


def GetHeaderFromPostname(postname, author, date, categories, image=None):
    postnameParts = postname.split('-')[3:]

    header = '---\n'

    # Title
    header += 'title: '
    for part in postnameParts:
        header += part.title() + ' '
    header += '\n'

    # Author
    header += 'author: ' + author + '\n'

    # Date
    header += 'date: ' + date + '\n'

    # Categories
    header += 'categories: ' + ''.join(categories) + '\n'

    # Pin
    header += 'pin: true\n'

    # Math
    header += 'math: true\n'

    # Mermaid
    header += 'mermaid: true\n'

    if image:
        header += 'image:\n'
        header += '\tpath' + image + '\n'
        header += '\tlqip: data:image/webp;base64,UklGRpoAAABXRUJQVlA4WAoAAAAQAAAADwAABwAAQUxQSDIAAAARL0AmbZurmr57yyIiqE8oiG0bejIYEQTgqiDA9vqnsUSI6H+oAERp2HZ65qP/VIAWAFZQOCBCAAAA8AEAnQEqEAAIAAVAfCWkAALp8sF8rgRgAP7o9FDvMCkMde9PK7euH5M1m6VWoDXf2FkP3BqV0ZYbO6NA/VFIAAAA\n'
        header += '\talt: image caption\n'

    # Close header
    header += '---\n'

    return header


def AddHeaderToPost(postname, header):
    # Append the post layout on top
    with open(postname + '.md', "r+") as fp:
        # Read lines list from file pointer
        lines = fp.readlines()

        # Insert header at index 0
        lines.insert(0, header)

        # Move the read cursor back to the beginning
        fp.seek(0)

        # Write lines to file
        fp.writelines(lines)


def AddDollarsAroundMatrices(postname):
    # Append the post layout on top
    with open(postname + '.md', "r+") as fp:
        # Read lines list from file pointer
        lines = fp.readlines()

        for i, line in enumerate(lines):
            if 'begin{matrix' in line or 'begin{array' in line:
                lines.pop(i)
                print('old: ' + line)
                line = '$' + line[:line.rfind('\n')] + '$\n'
                print('new: ' + line)
                lines.insert(i, line)

        # Move the read cursor back to the beginning
        fp.seek(0)

        # Write lines to file
        fp.writelines(lines)

if __name__ == '__main__':
    # Loop over all notebooks
    for notebookFilePath in glob.iglob(os.path.join(rootDir, '**/*.ipynb'), recursive=True):
        notebookFilename = notebookFilePath.split('/')[-1]
        notebookDir = notebookFilePath[:notebookFilePath.rfind(notebookFilename)]

        # Get category name (between _posts and xxx.ipynb, everything is the category name)
        rightHalf = notebookFilePath.split('_posts')[-1]
        categoriesJoined = rightHalf.split(notebookFilename)[0]
        categories = [x for x in categoriesJoined.split('/') if len(x)]

        ConsoleLog('Changing directory to: ' + notebookDir)
        ConsoleLog('Processing file: ' + notebookFilename)

        # Change dir to this file
        os.chdir(notebookDir)
        
        # Get notebook file creation date
        creationDate = GetFileCreationDate(notebookFilename)
        yearMonthDay, hoursMinuteSeconds, zone = creationDate.split(' ')

        ConsoleLog('Creation date: ' + yearMonthDay)
        ConsoleLog('Creation time: ' + hoursMinuteSeconds)
        ConsoleLog('Creation zone: ' + zone)

        # Post name
        postname = yearMonthDay + '-' + notebookFilename.split(".ipynb")[0]

        # Convert to markdown
        subprocess.run(['jupyter-nbconvert', notebookFilename, '--to', 'markdown', '--output', postname])

        # Get the markdownFilePath
        ConsoleLog('Created: ' + postname + '.md')

        # Get post header for this post
        header = GetHeaderFromPostname(postname, 'vector', creationDate, categories)
        ConsoleLog('Adding header:\n' + header)

        # Add header to post
        AddHeaderToPost(postname, header)

        AddDollarsAroundMatrices(postname)

        # Remove notebooks if deploying static website for hosting (to make the site light-weight)
        if args.deploy:
            print("Removing notebooks")
            subprocess.run(["sudo", "rm", notebookFilename])

        # Go back one dir
        os.chdir('..')
