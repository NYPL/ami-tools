import argparse
import logging
import os
import glob
import subprocess

# All about command line usage
def _make_parser():
  """
  Specify potential command line arguments.
  """
  parser = argparse.ArgumentParser()
  parser.description = 'evaluate the technical metadata of AMI files against specs'
  parser.add_argument('-d', '--directory',
                      help = 'Path to some parent directory of AMI files',
                      required = True)
  parser.add_argument('--log', help='The name of the log file')
  parser.add_argument('--quiet', action='store_true')
  #What other arguements would be helpful?

  return parser



# All about logging
LOGGER = logging.getLogger(__name__)

def _configure_logging(args):
  """
  Give options on how to report progress.
  Requires command line arguments for reporting level and where to save the log file
  """
  log_format = '%(asctime)s - %(levelname)s - %(message)s'
  if args.quiet:
    level = logging.WARNING
  else:
    level = logging.INFO
  if args.log:
    logging.basicConfig(filename=args.log, level=level, format=log_format)
  else:
    logging.basicConfig(level=level, format=log_format)


# Workhorse of this script, defines the workflow
def main():
  """
  Loop through all AMI files in a directory and compare them against MediaConch policies
  """
  # get command line arguments
  parser = _make_parser()
  args = parser.parse_args()

  # make sure that the directory actually exists and store its full path
  if os.path.exists(args.directory):
    directory = os.path.abspath(args.directory)
  else:
    LOGGER.error('Can't find directory: {}'.format(args.directory))

  # Find all of the AMI files
  # list to hold all the file paths
  ami_files = []

  # os.path.join adds '/' between the arguments we give it
  # this will be /path/to/directory/**/*pm.mov
  # ** is 'match any directory or series of directories'
  # *pm.mov is 'match any string that ends in pm.mov'
  video_pm_pattern = os.path.join(directory, '**', '*pm.mov')

  # glob.iglob does all the magical recursive searching for us
  for ami_filepath in glob.iglob(video_pm_filenames, recursive = True):
    ami_files.append(ami_filepath)

  #TODO loops to add all of the PM audio and SC video to our list of files
  audio_pm_pattern =


  # Locate our policies files
  #TODO create list to hold filenames of policies


  #TODO define a filename pattern so we can find the policy files
  policy_pattern = os.path.join()

  #TODO create for loop to find add all the policies to the list
  for policy_filepath in :


  # Check all of the files against our policies
  for ami_filepath in ami_files:
    LOGGER.info('Checking file: {}'.format(filepath))
    #TODO add list that contains filename policies
    for policy_filepath in :
      # subprocess.call() defines a bash command
      # it concatenates arguments like os.path.join() except with a space
      # it also lets us redirect standard output (like '>')
      #TODO add the ami_filepath into the command
      #TODO add a path where you want the report to go

      subprocess.call(['mediaconch', '-p', policy_filepath, , '-f']
                      stdout=open('path/to/report', 'w'),
                      stderr=subprocess.STDOUT
                      )
      #TODO above should be "mediaconch -fc -p policy_filepath list-of-files" for csv report

  # The current command runs every policy against every file
  # It overwrites the results onto the same file
  #  - If report is named dateAndTImeOfReport.csv, will this eliminate ovrwriting?
  # What do you need to make it write reports for each ami_file to different report files?
  # - if report is in csv format, each row = different file [this is good]
  # What do you need to do to make sure it only records successful reports?
  # - "successful" = ?
  # What do you need to do to report if a file doesn't pass any report?
  # - would be nifty to print list of fails








# Make sure that if we just call this script, it runs the main() function
# We put it at the end of the file to make sure everything else we've written has been read and parsed
if __name__ == "__main__":
  main()
