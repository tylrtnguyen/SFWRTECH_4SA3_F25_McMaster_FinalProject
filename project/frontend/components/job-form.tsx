"use client"

import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { Plus, X, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { getIndustries, addIndustry } from "@/lib/industry-storage"

const applicationStatuses = [
  "Interested",
  "Applied",
  "Interviewing",
  "Interviewed-Passed",
  "Interviewed-Failed",
] as const

const jobFormSchema = z.object({
  jobTitle: z.string().min(1, "Job title is required"),
  company: z.string().min(1, "Company name is required"),
  location: z.string().min(1, "Location is required"),
  source: z.string().optional(),
  jobDescription: z.string().min(1, "Job description is required"),
  industry: z.string().min(1, "Industry is required"),
  applicationStatus: z.enum(applicationStatuses, {
    required_error: "Application status is required",
  }),
})

export type JobFormData = z.infer<typeof jobFormSchema>

interface JobFormProps {
  onSubmit: (data: JobFormData) => void | Promise<void>
  isSubmitting?: boolean
}

export function JobForm({ onSubmit, isSubmitting: externalIsSubmitting = false }: JobFormProps) {
  const [industries, setIndustries] = useState<string[]>([])
  const [showCustomIndustry, setShowCustomIndustry] = useState(false)
  const [customIndustry, setCustomIndustry] = useState("")
  const [loadingIndustries, setLoadingIndustries] = useState(true)

  useEffect(() => {
    const loadIndustries = async () => {
      try {
        const industryList = await getIndustries()
        setIndustries(industryList)
      } catch (error) {
        console.error("Failed to load industries:", error)
        // Set basic fallback
        setIndustries(["Technology", "Healthcare", "Finance", "Education", "Other"])
      } finally {
        setLoadingIndustries(false)
      }
    }

    loadIndustries()
  }, [])

  const {
    register,
    handleSubmit,
    formState: { errors, touchedFields, isSubmitting },
    setValue,
    watch,
    reset,
  } = useForm<JobFormData>({
    resolver: zodResolver(jobFormSchema),
    defaultValues: {
      source: "",
    },
  })

  const selectedIndustry = watch("industry")
  const isCustomIndustry = selectedIndustry === "__custom__"

  const handleAddCustomIndustry = async () => {
    if (customIndustry.trim()) {
      try {
        await addIndustry(customIndustry.trim())
        // Refresh industries list
        const updatedIndustries = await getIndustries()
        setIndustries(updatedIndustries)
        setValue("industry", customIndustry.trim(), { shouldValidate: true })
        setCustomIndustry("")
        setShowCustomIndustry(false)
      } catch (error) {
        console.error("Failed to add custom industry:", error)
        // Still allow the user to select it even if API failed
        const normalized = customIndustry.trim()
        if (normalized && !industries.includes(normalized)) {
          const updated = [...industries, normalized].sort()
          setIndustries(updated)
          setValue("industry", normalized, { shouldValidate: true })
        }
        setCustomIndustry("")
        setShowCustomIndustry(false)
      }
    }
  }

  const onFormSubmit = async (data: JobFormData) => {
    await onSubmit(data)
    // Reset will be handled by parent component on success
  }

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Job Title */}
        <div className="space-y-2">
          <Label htmlFor="jobTitle" className="text-text-primary dark:text-[#e4e6eb]">
            Job Title <span className="text-destructive">*</span>
          </Label>
          <Input
            id="jobTitle"
            {...register("jobTitle")}
            placeholder="e.g., Software Engineer"
            className={
              touchedFields.jobTitle && errors.jobTitle
                ? "border-destructive focus-visible:ring-destructive"
                : ""
            }
          />
          {touchedFields.jobTitle && errors.jobTitle && (
            <p className="text-sm text-destructive">{errors.jobTitle.message}</p>
          )}
        </div>

        {/* Company */}
        <div className="space-y-2">
          <Label htmlFor="company" className="text-text-primary dark:text-[#e4e6eb]">
            Company <span className="text-destructive">*</span>
          </Label>
          <Input
            id="company"
            {...register("company")}
            placeholder="e.g., Tech Corp"
            className={
              touchedFields.company && errors.company
                ? "border-destructive focus-visible:ring-destructive"
                : ""
            }
          />
          {touchedFields.company && errors.company && (
            <p className="text-sm text-destructive">{errors.company.message}</p>
          )}
        </div>

        {/* Location */}
        <div className="space-y-2">
          <Label htmlFor="location" className="text-text-primary dark:text-[#e4e6eb]">
            Location <span className="text-destructive">*</span>
          </Label>
          <Input
            id="location"
            {...register("location")}
            placeholder="e.g., San Francisco, CA"
            className={
              touchedFields.location && errors.location
                ? "border-destructive focus-visible:ring-destructive"
                : ""
            }
          />
          {touchedFields.location && errors.location && (
            <p className="text-sm text-destructive">{errors.location.message}</p>
          )}
        </div>

        {/* Source */}
        <div className="space-y-2">
          <Label htmlFor="source" className="text-text-primary dark:text-[#e4e6eb]">
            Source (Optional)
          </Label>
          <Input
            id="source"
            {...register("source")}
            placeholder="e.g., LinkedIn, Indeed"
          />
        </div>

        {/* Industry */}
        <div className="space-y-2">
          <Label htmlFor="industry" className="text-text-primary dark:text-[#e4e6eb]">
            Industry <span className="text-destructive">*</span>
          </Label>
          <div className="space-y-2">
            <Select
              value={selectedIndustry || ""}
              onValueChange={(value) => {
                if (value === "__custom__") {
                  setShowCustomIndustry(true)
                } else {
                  setValue("industry", value, { shouldValidate: true })
                  setShowCustomIndustry(false)
                }
              }}
              disabled={loadingIndustries || externalIsSubmitting}
            >
              <SelectTrigger
                className={
                  touchedFields.industry && errors.industry
                    ? "border-destructive focus-visible:ring-destructive"
                    : ""
                }
              >
                <SelectValue placeholder={loadingIndustries ? "Loading industries..." : "Select industry"} />
              </SelectTrigger>
              <SelectContent>
                {industries.map((industry) => (
                  <SelectItem key={industry} value={industry}>
                    {industry}
                  </SelectItem>
                ))}
                <SelectItem value="__custom__">
                  <div className="flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Add custom industry
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            {showCustomIndustry && (
              <div className="flex gap-2">
                <Input
                  placeholder="Enter custom industry"
                  value={customIndustry}
                  onChange={(e) => setCustomIndustry(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault()
                      handleAddCustomIndustry()
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={handleAddCustomIndustry}
                >
                  <Plus className="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    setShowCustomIndustry(false)
                    setCustomIndustry("")
                    setValue("industry", "", { shouldValidate: false })
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
          {touchedFields.industry && errors.industry && (
            <p className="text-sm text-destructive">{errors.industry.message}</p>
          )}
        </div>

        {/* Application Status */}
        <div className="space-y-2">
          <Label htmlFor="applicationStatus" className="text-text-primary dark:text-[#e4e6eb]">
            Application Status <span className="text-destructive">*</span>
          </Label>
          <Select
            value={watch("applicationStatus") || ""}
            onValueChange={(value) =>
              setValue("applicationStatus", value as JobFormData["applicationStatus"], {
                shouldValidate: true,
              })
            }
          >
            <SelectTrigger
              className={
                touchedFields.applicationStatus && errors.applicationStatus
                  ? "border-destructive focus-visible:ring-destructive"
                  : ""
              }
            >
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              {applicationStatuses.map((status) => (
                <SelectItem key={status} value={status}>
                  {status}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {touchedFields.applicationStatus && errors.applicationStatus && (
            <p className="text-sm text-destructive">
              {errors.applicationStatus.message}
            </p>
          )}
        </div>
      </div>

      {/* Job Description - Full Width */}
      <div className="space-y-2">
        <Label htmlFor="jobDescription" className="text-text-primary dark:text-[#e4e6eb]">
          Job Description <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="jobDescription"
          {...register("jobDescription")}
          placeholder="Enter job description..."
          className={`min-h-[200px] ${
            touchedFields.jobDescription && errors.jobDescription
              ? "border-destructive focus-visible:ring-destructive"
              : ""
          }`}
        />
        {touchedFields.jobDescription && errors.jobDescription && (
          <p className="text-sm text-destructive">
            {errors.jobDescription.message}
          </p>
        )}
      </div>

      {/* Submit Button */}
      <Button type="submit" className="w-full" disabled={externalIsSubmitting}>
        {externalIsSubmitting ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Analyzing and Saving Job...
          </>
        ) : (
          "Save Job"
        )}
      </Button>
    </form>
  )
}

